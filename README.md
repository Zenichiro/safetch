# safetch

safetch is a small VPN-aware wget wrapper for safely downloading files through a configured proxy, initially Gluetun. It checks the VPN/proxy path before downloading, fails closed if the check fails, and never falls back to a direct connection.