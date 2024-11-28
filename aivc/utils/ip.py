import requests
import netifaces
import ipaddress

def is_private_ip(ip_address: str) -> bool:
    ip = ipaddress.ip_address(ip_address)
    return (
        ip.is_private or
        ip.is_loopback or
        ip.is_link_local or
        ip.is_multicast or
        ip.is_reserved or
        ip.is_unspecified
    )

def get_local_address(interfaces:list=["eth0", "en0"]):
    m = local_addresses()
    for itf in interfaces:
        if itf in m:
            return m[itf]
    return ""

def local_addresses():
    m = {}
    ifaces = netifaces.interfaces()

    for i in ifaces:
        addrs = netifaces.ifaddresses(i).get(netifaces.AF_INET)
        if addrs:
            for a in addrs:
                ip = a['addr']
                if not ipaddress.ip_address(ip).is_loopback and ipaddress.ip_address(ip).version == 4:
                    m[i] = ip

    return m

def get_eip():
    url = "https://urtc.com.cn/uschedule"
    data = {"Action": "GetRequestIp"}
    try:
        response = requests.post(url, json=data, timeout=3)
        ip = response.json().get("Ip", "")
        print(f"GetEIP from {url}: {ip}")
        return ip
    except Exception as e:
        print(f"GetEIP from {url} error: {e}")
        return ""

def get_eip_v0():
    url = "http://ipinfo.io/ip"
    print("GetEIP from", url)
    try:
        resp = requests.get(url, timeout=3)
        resp.raise_for_status()
        ip_str = resp.text.strip()
        return ip_str, None
    except Exception as err:
        return "", err

def get_ip():
    eip = get_eip()
    if eip:
        return eip
    eip_v0 = get_eip_v0()
    if eip_v0[0]:
        return eip_v0[0]
    return get_local_address()

IP = get_ip()

if __name__ == "__main__":
    print(IP)