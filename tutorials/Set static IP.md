### **Step-by-Step Guide to Set a Manual IP (10.0.0.254) on "Wired connection 1"**  

#### **1. Check Existing Connections**  
First, verify the exact name of your wired connection:  
```bash
nmcli connection show
```
Look for `"Wired connection 1"` (or similar).  

#### **2. Set a Static IPv4 Address**  
Run:  
```bash
nmcli connection modify "Wired connection 1" \
    ipv4.method manual \
    ipv4.addresses "10.0.0.254/24" \
    ipv4.gateway "10.0.0.1" \
    ipv4.dns "8.8.8.8,8.8.4.4"
```
- `ipv4.method manual` → Disables DHCP, enables static IP.  
- `ipv4.addresses "10.0.0.254/24"` → Sets IP `10.0.0.254` with subnet `/24` (`255.255.255.0`).  
- `ipv4.gateway "10.0.0.1"` → (Optional) Sets default gateway.  
- `ipv4.dns "8.8.8.8,8.8.4.4"` → (Optional) Sets Google DNS.  

> **Note:**  
> - If you **only** need the IP (no gateway/DNS), just set `ipv4.method` and `ipv4.addresses`.  

#### **3. Restart the Connection**  
Apply changes by restarting the connection:  
```bash
nmcli connection down "Wired connection 1" && nmcli connection up "Wired connection 1"
```

#### **4. Verify the New IP**  
Check if the IP was assigned correctly:  
```bash
hostname -I
```
or:  
```bash
nmcli connection show "Wired connection 1" | grep ipv4.addresses
```

#### **5. Test Network Connectivity**  
Ping your gateway (or another device on the network):  
```bash
ping 10.0.0.1
```
If no response, check:  
- Firewall rules (`sudo ufw status`).  
- Correct gateway/DNS settings.  

---

### **Troubleshooting**  
#### **Issue 1: "Connection 'Wired connection 1' not found"**  
- **Fix:** List all connections with `nmcli connection show` and use the **exact** name (case-sensitive).  

#### **Issue 2: IP Doesn’t Apply After Restart**  
- **Fix:** Reload NetworkManager:  
  ```bash
  sudo systemctl restart NetworkManager
  ```

#### **Issue 3: No Internet Access**  
- **Fix:** Ensure:  
  - Gateway (`10.0.0.1`) is correct.  
  - DNS is set (`nmcli con mod "Wired connection 1" ipv4.ignore-auto-dns no` if needed).  
