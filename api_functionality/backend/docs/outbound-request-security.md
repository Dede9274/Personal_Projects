# Outbound request security

Monitor checks are server-side HTTP requests, so every configured URL is
treated as untrusted input. The application applies the same outbound target
policy when a monitor is created or updated and again immediately before the
worker sends each request.

## Policy

A permitted target must:

- use `http` or `https`;
- include a hostname and no embedded username or password;
- contain no backslashes or control characters;
- resolve entirely to globally reachable unicast IP addresses.

The resolved-address check rejects private, loopback, link-local, multicast,
reserved, and unspecified IPv4 and IPv6 addresses. Because every address in a
DNS response must pass, a mixed public/private answer is rejected as well.

Automatic HTTPX redirects are disabled. The checker follows HTTP 301, 302, 303,
307, and 308 responses itself, resolves and validates every `Location` target,
and stops after five redirects. Arbitrary ports remain allowed when the target
is public.

## Rejected checks

Worker-side policy failures are stored with `security_rejected=true` and shown
as **Blocked** in the dashboard. They do not increment failure streaks, open
incidents, resolve active incidents, or reduce availability percentages. This
keeps a configuration/security problem distinct from an unavailable endpoint.

## Defense in depth

Application validation substantially reduces SSRF exposure, but DNS resolution
and the HTTP connection are still separate operations. Production deployments
should also enforce egress filtering at the container, host, or network layer
so monitor workers cannot reach loopback, private subnets, link-local networks,
cloud metadata services, or internal service ports even if application checks
are bypassed.
