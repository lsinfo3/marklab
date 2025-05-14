# MMCLI commands used by operator setup

## Basics

- L: List available modems.
- **M:** List available modems and monitor modems added or removed.
- **S:** Scan for any potential new modems. This is only useful when expecting pure RS232 modems, as they are not notified automatically by the kernel.
- **m, --modem=[PATH|INDEX]:** Specify a modem.
- m INDEX —**3gpp-scan:** Scan for available 3GPP networks
    - don’t forget to set timeout

```bash
mmcli -m 0
```

## Activate data connection

```bash
mmcli -m 0 --enable
```


```bash
mmcli -m 0 --simple-connect='apn=em,ip-type=ipv4’
```

→ Get IP-Address and Interface from bearer information (here: 1)

```bash
sudo mmcli -m 0 --bearer=1
```

- Set up an interface (here: wwan0, from bearer information above)
    
```bash
ip link set wwan0 up
```
    
- Flush all configuration for a given interface
    
```bash
ip addr flush dev
```
    
- Set the IPv4 address acquired from bearer information above, the CIDR subnet mask can always be set to 32:
    
```bash
ip addr add 10.189.104.55/32 dev wwan0
```
    

### Test connection

```bash
ping -I wwan0 google.com
```

### Get signal strength

```bash
mmcli -m 5 --signal-setup=5
mmcli -m 5 --signal-get
```

### Change operator (after scanning for available networks)

Scan 
```bash
- mmcli -m 0 --3gpp-scan --timeout=120
```

Change operator
```bash
- mmcli -m 0 --simple-disconnect
- mmcli -m 0 --3gpp-register-in-operator=26201
- mmcli -m 0 --simple-connect='apn=em,ip-type=ipv4'
```