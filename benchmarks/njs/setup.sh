apt-get update && apt-get install -y make autoconf automake libtool libpcre3-dev
# hg.nginx.org is retired and FuzzBench's hash d2877d60 is not in the GitHub mirror; c45e5cee is the last commit before FuzzBench's commit_date 2020-02-18 04:02 UTC.
git clone https://github.com/nginx/njs.git njs
git -C njs checkout -f c45e5cee84c4c7bbd4a2d461ade05cfd11f112c2
