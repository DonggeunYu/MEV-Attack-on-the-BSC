# IAC

## Ethereum Node
### Check Geth

To see the process id, run this command:

~~~
ps -A | grep geth
~~~

Check the logs to see if the process started correctly:

~~~
tail /data/geth/logs/geth.log
~~~

Output:

~~~
Looking for peers                        peercount=1 tried=27 static=0
Post-merge network, but no beacon client seen. Please launch one to follow the chain!
~~~

### Check Lighthouse

To see the process id, run the following command:

~~~
ps -A | grep lighthouse
~~~

Check the log file to see if the process started correctly. This may take a few minutes to show up:

~~~
tail -f /data/lighthouse/logs/lighthouse.log
~~~

Output:

~~~
INFO Syncing
INFO Synced
INFO New block received
~~~

Check the Geth log again to confirm that the logs are being generated correctly.

~~~
tail -f /data/geth/logs/geth.log
~~~

Output:

~~~
Syncing beacon headers
~~~

### Check the Sync Status
Run the following Geth command to check if the node is still syncing. Output of "false" means that
it is synced with the network.

~~~
geth attach /data/geth/chaindata/geth.ipc
~~~

At the Geth console execute:

~~~
eth.syncing
~~~

Output:

~~~
#If not synced:

{
currentBlock: 5186007,
healedBytecodeBytes: 0,
healedBytecodes: 0,
healedTrienodeBytes: 0,
healedTrienodes: 0,
healingBytecode: 0,
healingTrienodes: 0,
highestBlock: 16193909,
startingBlock: 0,
syncedAccountBytes: 2338698797,
syncedAccounts: 9417189,
syncedBytecodeBytes: 302598044,
syncedBytecodes: 58012,
syncedStorage: 42832820,
syncedStorageBytes: 9263550660
}

#If synced:

false
~~~

### Test the RPC endpoint

~~~
curl -H "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_syncing","id":67}' http://$EXT_IP_ADDRESS:8545 | jq
~~~


## Size up the Persistent Disk

Check the persistent disk path:

~~~
ddonggeunn@instance-2:~$ ls -al /dev/disk/by-id/
total 0
drwxr-xr-x 2 root root 240 Feb  3 09:20 .
drwxr-xr-x 7 root root 140 Feb  3 09:20 ..
lrwxrwxrwx 1 root root   9 Feb  3 09:20 google-ethereum-node-disk -> ../../sdb
...
~~~

Mount the disk to the `/data` directory:

~~~
ddonggeunn@instance-2:~$ sudo mount /dev/disk/by-id/google-eth-rpc-node-disk /data
~~~

Check the disk size:

~~~
ddonggeunn@instance-2:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       9.6G  2.0G  7.6G  21% /
devtmpfs        2.0G     0  2.0G   0% /dev
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           391M  952K  390M   1% /run
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
/dev/loop0       64M   64M     0 100% /snap/core20/2105
/dev/loop1      369M  369M     0 100% /snap/google-cloud-cli/207
/dev/loop2       92M   92M     0 100% /snap/lxd/24061
/dev/loop3       41M   41M     0 100% /snap/snapd/20671
/dev/sda15      105M  6.1M   99M   6% /boot/efi
tmpfs           391M     0  391M   0% /run/user/1001
/dev/sdb       1007G  955G  1.2G 100% /data
~~~

Resize the disk:

~~~
ddonggeunn@instance-2:~$ sudo resize2fs /dev/sdb
resize2fs 1.45.5 (07-Jan-2020)
Filesystem at /dev/sdb is mounted on /data; on-line resizing required
old_desc_blocks = 128, new_desc_blocks = 192
The filesystem on /dev/sdb is now 402653184 (4k) blocks long.
~~~

Check the disk size again:

~~~
ddonggeunn@instance-2:~$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       9.6G  2.0G  7.6G  21% /
devtmpfs        2.0G     0  2.0G   0% /dev
tmpfs           2.0G     0  2.0G   0% /dev/shm
tmpfs           391M  952K  390M   1% /run
tmpfs           5.0M     0  5.0M   0% /run/lock
tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
/dev/loop0       64M   64M     0 100% /snap/core20/2105
/dev/loop1      369M  369M     0 100% /snap/google-cloud-cli/207
/dev/loop2       92M   92M     0 100% /snap/lxd/24061
/dev/loop3       41M   41M     0 100% /snap/snapd/20671
/dev/sda15      105M  6.1M   99M   6% /boot/efi
tmpfs           391M     0  391M   0% /run/user/1001
/dev/sdb        1.5T  955G  485G  67% /data
~~~
