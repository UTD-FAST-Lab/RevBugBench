apt-get update && apt-get install -y make autoconf automake autogen pkg-config libtool flex bison wget
git clone https://github.com/ntop/nDPI.git ndpi
git -C ndpi checkout -f 98d9f524f9ff7746d0345939fe543020f8057212
[ -f libpcap-1.9.1.tar.gz ] || wget -q https://www.tcpdump.org/release/libpcap-1.9.1.tar.gz
