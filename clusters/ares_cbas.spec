[clusters]
ares =
    172.23.133.13:kv
    172.23.133.11:cbas
    172.23.133.12:cbas
    172.23.133.14:kv

[clients]
hosts =
    172.23.133.10
credentials = root:couchbase

[storage]
data = /data
index = /data

[credentials]
rest = Administrator:password
ssh = root:couchbase

[parameters]
OS = CentOS 7
CPU = E5-2630 v4 (40 vCPU)
Memory = 64 GB
Disk = Samsung SM863
