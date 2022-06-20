import time
import datetime
import dns.reversename
import dns.resolver
import io
import ipaddress
import json
import traceback
import sqlite3



def _parse_asinfo_stream(stream):
    asinfo_list = []
    asinfo = {}
    asinfo_prev_key = ""
    while l := stream.readline():
        if len(l) == 1:
            asinfo = {}
            asinfo_list.append(asinfo)
            continue
        kv = [e.strip() for e in l.split(":", 1)]
        if len(kv) == 2:
            asinfo[kv[0]] = kv[1]
            asinfo_prev_key = kv[0]
        elif len(kv) == 1:
            asinfo[asinfo_prev_key] += kv[0]
        else:
            print("err")

    return asinfo_list

def _get_reverse_dns_name_by_nw(ipnetwork):
    test_ip = next(ipnetwork.hosts())

    result = {"expires": None, "nameserver": None, "resp": None, "err": None}
    result["network"] = str(ipnetwork)
    result["requested_at"] = datetime.datetime.now(tz=datetime.timezone.utc)

    rev_addr = dns.reversename.from_address(str(test_ip))
    result["query"] = rev_addr.to_text()

    try:
        rev_ip = dns.resolver.resolve(rev_addr, 'PTR')
        result["resp"] = rev_ip[0].to_text()
        result["expires"] = rev_ip.expiration
        result["nameserver"] = rev_ip.nameserver
    except dns.resolver.NoNameservers:
        result["err"] = "NoNameservers"
    except dns.resolver.NXDOMAIN:
        result["err"] = "NXDOMAIN"
    except Exception as exc:
        print(traceback.format_exc())
        raise exc

    return result

asinfo_stream = open("as2497.txt", "r")
asinfo_list = _parse_asinfo_stream(asinfo_stream)

dns_cache_db = sqlite3.connect('dns_cache.db')
with dns_cache_db:
    dns_cache_db.execute("CREATE TABLE IF NOT EXISTS dns(id INTEGER PRIMARY KEY, requested_at DATETIME, expires DATETIME, nameserver TEXT, network TEXT, query TEXT, resp TEXT, err TEXT);")

dns_cache = set([e[0] for e in dns_cache_db.execute("SELECT network FROM dns").fetchall()])


iij_route_list = [e for e in asinfo_list if "IIJ IPv4 BLOCK" in e["descr"]]
for route_info in iij_route_list:
    network = ipaddress.ip_network(route_info["route"])

    network_list = [network]
    if network.prefixlen < 24:
        network_list = network.subnets(new_prefix=24)
    print("checking {}".format(network))

    for network in network_list:
        if str(network) in dns_cache:
            continue

        revdns = _get_reverse_dns_name_by_nw(network)
        print(revdns)
        with dns_cache_db:
            dns_cache_db.execute("INSERT INTO dns(requested_at, expires, nameserver, network, query, resp, err) VALUES(:requested_at, :expires, :nameserver, :network, :query, :resp, :err);", revdns)
        time.sleep(4)


"""

counts = 0
for route in iij_route_list:
    ipnw = ipaddress.ip_network(route["route"])

    if ipnw.prefixlen < 24:
        sn = list(ipnw.subnets(new_prefix=24))
        counts += len(sn)
        for subnet in sn:
            testip = next(subnet.hosts())
            result = dns.reversename.from_address(str(testip))
            try:
                result2 = dns.resolver.resolve(result, 'PTR')
                .to_text().endswith(".rev.vmobile.jp.")
                breakpoint()
                with open("revdns/{}.txt".format(subnet), "w") as f:
                    f.write(result[2])
                print(result2)
            except:
                pass
            print(result)
            print(testip)
            breakpoint()
        breakpoint()
        # print(route)
        # print(sn)
        # print(json.dumps(iij_route_list))
#    print(route)
#    os.system("")
#    breakpoint()



print(counts)
        .to_text().endswith(".rev.vmobile.jp.")
        breakpoint()
        with open("revdns/{}.txt".format(subnet), "w") as f:
            f.write(result[2])
        print(result2)
"""
