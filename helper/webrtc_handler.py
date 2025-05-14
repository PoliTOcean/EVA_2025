import asyncio
import json
import ssl
import websockets
import threading
import base64
from datetime import datetime
import os

class JanusWebRTCHandler:
    def __init__(self):
        self.server_url = None
        self.janus_session_id = None
        self.janus_handles = {}
        self.streams_info = {}
        self.connection_status = "Disconnected"
        self.status_callback = None
        self.websocket = None
        self.connected = False
        self.transaction_callbacks = {}
        self.next_transaction_id = 1
        self.ws_thread = None
        self.loop = None
        
    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.status_callback = callback
        
    def update_status(self, status):
        """Update connection status and notify callback"""
        self.connection_status = status
        if self.status_callback:
            self.status_callback(status)
    
    def connect(self, server_ip, port=8188, use_ssl=True, on_success=None, on_error=None):
        """Connect to Janus WebRTC Gateway
        
        Args:
            server_ip: IP address of Janus server
            port: Port number (default: 8188)
            use_ssl: Whether to use secure WebSocket (default: True)
            on_success: Callback for successful connection
            on_error: Callback for connection errors
        """
        protocol = "wss" if use_ssl else "ws"
        self.server_url = f"{protocol}://{server_ip}:{port}/janus"
        
        # Start connection in a separate thread to avoid blocking UI
        def connect_thread():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            try:
                self.update_status("Connecting...")
                self.loop.run_until_complete(self._connect_async(use_ssl, on_success, on_error))
            except Exception as e:
                error_msg = str(e)
                if "WRONG_VERSION_NUMBER" in error_msg:
                    # This typically happens when trying to use wss:// for a non-SSL server
                    error_msg = "SSL Error: The server might not support SSL. Try connecting without SSL."
                    
                    # Auto-retry with non-SSL if we were using SSL
                    if use_ssl:
                        self.update_status("Retrying without SSL...")
                        try:
                            protocol = "ws"
                            self.server_url = f"{protocol}://{server_ip}:{port}/janus"
                            self.loop.run_until_complete(self._connect_async(False, on_success, on_error))
                            return
                        except Exception as retry_e:
                            error_msg = f"Failed again without SSL: {str(retry_e)}"
                
                self.update_status(f"Error: {error_msg}")
                if on_error:
                    self.loop.call_soon_threadsafe(lambda: on_error(error_msg))
        
        self.ws_thread = threading.Thread(target=connect_thread)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    async def _connect_async(self, use_ssl, on_success, on_error):
        """Async implementation of the connection logic"""
        # SSL context that accepts self-signed certificates
        ssl_context = None
        if use_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            self.websocket = await websockets.connect(
                self.server_url,
                ssl=ssl_context
            )
            self.connected = True
            
            # Start message handling loop
            asyncio.create_task(self._message_loop())
            
            # Create a session
            await self._create_session()
            
            # Discover available streams
            await self._discover_streams()
            
            # Call success callback in the main thread
            if on_success:
                # Using a local variable to capture the streams_info
                streams = self.streams_info
                self.loop.call_soon_threadsafe(lambda: on_success(streams))
                
            self.update_status("Connected")
            
        except Exception as e:
            self.connected = False
            self.update_status(f"Connection failed: {str(e)}")
            if on_error:
                # Fix the variable capture issue by using a default parameter
                error_msg = str(e)
                self.loop.call_soon_threadsafe(lambda error=error_msg: on_error(error))
            raise
    
    async def _message_loop(self):
        """Handle incoming WebSocket messages"""
        while self.connected:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle transaction callbacks
                transaction = data.get("transaction")
                if transaction and transaction in self.transaction_callbacks:
                    callback_func = self.transaction_callbacks[transaction]
                    callback_func(data)
                    del self.transaction_callbacks[transaction]
                
                # Handle events
                if data.get("janus") == "event":
                    # Handle plugin events
                    pass
                
            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                self.update_status("Disconnected")
                break
            except Exception as e:
                print(f"Error in message loop: {str(e)}")
    
    async def _create_session(self):
        """Create a Janus session"""
        transaction = str(self.next_transaction_id)
        self.next_transaction_id += 1
        
        message = {
            "janus": "create",
            "transaction": transaction
        }
        
        response = await self._send_request(message)
        if response.get("janus") == "success":
            self.janus_session_id = response.get("data", {}).get("id")
            self.update_status("Session created")
        else:
            raise Exception("Failed to create Janus session")
    
    async def _discover_streams(self):
        """Discover available camera streams"""
        # Attach to streaming plugin
        streaming_handle = await self._attach_plugin("janus.plugin.streaming")
        
        # List available streams
        transaction = str(self.next_transaction_id)
        self.next_transaction_id += 1
        
        message = {
            "janus": "message",
            "body": {
                "request": "list"
            },
            "transaction": transaction,
            "session_id": self.janus_session_id,
            "handle_id": streaming_handle
        }
        
        response = await self._send_request(message)
        if response.get("janus") == "success":
            streams_list = response.get("plugindata", {}).get("data", {}).get("list", [])
            
            # Store stream information
            for stream in streams_list:
                stream_id = stream.get("id")
                stream_name = stream.get("description", f"Camera {stream_id}")
                self.streams_info[stream_id] = {
                    "id": stream_id,
                    "name": stream_name,
                    "handle_id": None
                }
            
            self.update_status(f"Discovered {len(self.streams_info)} streams")
        else:
            raise Exception("Failed to discover streams")
    
    async def _attach_plugin(self, plugin):
        """Attach to a Janus plugin"""
        transaction = str(self.next_transaction_id)
        self.next_transaction_id += 1
        
        message = {
            "janus": "attach",
            "plugin": plugin,
            "transaction": transaction,
            "session_id": self.janus_session_id
        }
        
        response = await self._send_request(message)
        if response.get("janus") == "success":
            handle_id = response.get("data", {}).get("id")
            return handle_id
        else:
            raise Exception(f"Failed to attach to plugin {plugin}")
    
    async def _send_request(self, message):
        """Send a request and wait for a response"""
        transaction = message.get("transaction")
        
        # Create a future to receive the response
        future = self.loop.create_future()
        
        # Set up callback
        def callback(response):
            if not future.done():
                future.set_result(response)
        
        self.transaction_callbacks[transaction] = callback
        
        # Send the message
        await self.websocket.send(json.dumps(message))
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=10.0)
            return response
        except asyncio.TimeoutError:
            del self.transaction_callbacks[transaction]
            raise Exception("Request timed out")
    
    def take_snapshot(self, stream_ids, on_success=None, on_error=None):
        """Take snapshots from the specified streams"""
        if not self.connected:
            if on_error:
                on_error("Not connected to Janus server")
            return
        
        # Ensure stream_ids is a list
        if not isinstance(stream_ids, list):
            stream_ids = [stream_ids]
        
        # Start snapshot capture in a thread
        def snapshot_thread():
            asyncio.set_event_loop(self.loop)
            future = asyncio.run_coroutine_threadsafe(
                self._take_snapshot_async(stream_ids), 
                self.loop
            )
            
            try:
                result = future.result(timeout=15.0)  # Wait up to 15 seconds
                if on_success:
                    on_success(result)
            except Exception as e:
                if on_error:
                    on_error(str(e))
        
        threading.Thread(target=snapshot_thread).start()
    
    async def _take_snapshot_async(self, stream_ids):
        """Async implementation of snapshot capture"""
        snapshots = {}
        
        for stream_id in stream_ids:
            # Check if we have this stream
            if stream_id not in self.streams_info:
                continue
                
            # Attach to the stream if not already attached
            if not self.streams_info[stream_id].get("handle_id"):
                handle_id = await self._attach_plugin("janus.plugin.streaming")
                self.streams_info[stream_id]["handle_id"] = handle_id
            
            handle_id = self.streams_info[stream_id]["handle_id"]
            
            # Request a snapshot
            transaction = str(self.next_transaction_id)
            self.next_transaction_id += 1
            
            message = {
                "janus": "message",
                "body": {
                    "request": "watch",
                    "id": stream_id,
                    "snapshot": True
                },
                "transaction": transaction,
                "session_id": self.janus_session_id,
                "handle_id": handle_id
            }
            
            response = await self._send_request(message)
            
            # Process the response to extract the snapshot
            if response.get("janus") == "success":
                # The actual snapshot should be in a subsequent event message
                # For this simplified implementation, we're assuming it works
                # In a real implementation, you would wait for the snapshot event
                
                # Simulate saving a snapshot
                snapshots[stream_id] = {
                    "stream_id": stream_id,
                    "name": self.streams_info[stream_id]["name"],
                    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
                }
                
                # Save the snapshot
                self._save_snapshot(stream_id, snapshots[stream_id])
            
        return snapshots
    
    def _save_snapshot(self, stream_id, snapshot_info):
        """Save a snapshot to file"""
        # In a real implementation, this would save actual image data
        # For this example, we just create a placeholder file
        folder_path = os.path.join("photos", str(stream_id))
        os.makedirs(folder_path, exist_ok=True)
        
        timestamp = snapshot_info["timestamp"]
        file_path = os.path.join(folder_path, f"{timestamp}.jpg")
        
        with open(file_path, "w") as file:
            file.write(f"Placeholder for snapshot from {snapshot_info['name']}")
        
        print(f"Snapshot saved to {file_path}")
    
    def disconnect(self):
        """Disconnect from Janus server"""
        if not self.connected:
            return
            
        def disconnect_thread():
            asyncio.set_event_loop(self.loop)
            future = asyncio.run_coroutine_threadsafe(
                self._disconnect_async(), 
                self.loop
            )
            try:
                future.result(timeout=5.0)
            except Exception as e:
                print(f"Error disconnecting: {str(e)}")
                
        threading.Thread(target=disconnect_thread).start()
    
    async def _disconnect_async(self):
        """Async implementation of disconnect logic"""
        if self.janus_session_id:
            # Destroy session
            transaction = str(self.next_transaction_id)
            self.next_transaction_id += 1
            
            message = {
                "janus": "destroy",
                "transaction": transaction,
                "session_id": self.janus_session_id
            }
            
            try:
                await self.websocket.send(json.dumps(message))
            except:
                pass  # Ignore errors during disconnect
        
        # Close websocket
        if self.websocket:
            await self.websocket.close()
            
        self.connected = False
        self.janus_session_id = None
        self.janus_handles = {}
        self.update_status("Disconnected")
