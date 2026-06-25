#!/usr/bin/env python3
"""Download IoT Connect OpenAPI specs and generate an MCP server config."""
import os
import sys
import json
from pathlib import Path

import requests


def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_discovery(skey, env, pf):
    version = '2.1' if pf == 'aws' else '2'
    url = f'https://discovery.iotconnect.io/api/uisdk/solutionkey/{skey}/env/{env}'
    print(f"Discovery: {url}?version={version}&pf={pf}")
    r = requests.get(url, params={'version': version, 'pf': pf}, timeout=30)
    if r.status_code != 200:
        die(f"Discovery failed ({r.status_code}): {r.text}")
    data = r.json().get('data')
    if not data:
        die(f"Discovery response missing 'data': {r.text}")
    return data


def swagger_url(base_url):
    # e.g. https://awspocevent.iotconnect.io/api/v2.1 -> https://awspocevent.iotconnect.io/swagger/v2.1/swagger.json
    return base_url.rstrip('/').replace('/api/', '/swagger/') + '/swagger.json'


def fetch_swagger(base_url):
    url = swagger_url(base_url)
    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except requests.exceptions.JSONDecodeError:
        return None


# Services confirmed to expose a valid swagger-json endpoint.
# Superuser/internal services (admin, authorize, agent, bigdata, etc.) are excluded.
SUPPORTED_SERVICES = {
    'auth',
    'dashboard',
    'device',
    'entity',
    'event',
    'file',
    'firmware',
    'telemetry',
}


def service_name(key):
    return key.lower().removesuffix('baseurl')


# Placeholder in the README template that gets replaced with the generated Services section.
README_PLACEHOLDER = '@@@SERVICES_TABLE@@@'


def discovery_label(key):
    """Strip the trailing 'BaseUrl' from a discovery key, preserving case. e.g. 'entityBaseUrl' -> 'entity'."""
    return key[:-len('BaseUrl')] if key.lower().endswith('baseurl') else key


def services_for_url(services, base_url):
    """
    All top-level service names from discovery that map to the given base URL.

    Discovery aliases several top-level names onto one physical microservice (one base URL), so
    this returns every such name rather than the single arbitrary one the script saved the file as.
    """
    target = base_url.rstrip('/')
    labels = [
        discovery_label(key)
        for key, url in services.items()
        if key.lower().endswith('baseurl') and url.rstrip('/') == target
    ]
    return sorted(labels, key=str.lower)


def build_readme_body(pulled):
    """Build the markdown that replaces the placeholder: one table mapping services to base URLs."""
    lines = [
        '| Top-level services | Base URL | Spec |',
        '| --- | --- | --- |',
    ]
    for entry in pulled:
        names = ', '.join(f'`{name}`' for name in entry['services'])
        lines.append(f"| {names} | `{entry['base_url']}` | [`{entry['name']}.json`]({entry['name']}.json) |")
    return '\n'.join(lines) + '\n'


def write_readme(template_path, out_path, pulled):
    """Render the README from the template by substituting the generated Services section."""
    if not template_path.exists():
        print(f"  WARN README template not found at {template_path}; skipping README", file=sys.stderr)
        return
    template = template_path.read_text()
    if README_PLACEHOLDER not in template:
        die(f"README template {template_path} is missing the {README_PLACEHOLDER} placeholder")
    out_path.write_text(template.replace(README_PLACEHOLDER, build_readme_body(pulled)))
    print(f"Wrote {out_path}")


def main():
    missing = [v for v in ('IOTC_SKEY', 'IOTC_ENV', 'IOTC_PF') if not os.environ.get(v)]
    if missing:
        die(f"Missing required env vars: {', '.join(missing)}")

    skey, env, pf = os.environ['IOTC_SKEY'], os.environ['IOTC_ENV'], os.environ['IOTC_PF']

    project_root = Path(__file__).parent.parent
    schemas_dir = project_root / 'work/mcp/schemas'
    schemas_dir.mkdir(parents=True, exist_ok=True)

    services = fetch_discovery(skey, env, pf)

    # Deduplicate by URL; restrict to known-good services (sorted for deterministic naming)
    unique = {}
    for key in sorted(k for k in services if 'BaseUrl' in k):
        name = service_name(key)
        if name not in SUPPORTED_SERVICES:
            continue
        url = services[key].rstrip('/')
        if url not in unique:
            unique[url] = name

    print(f"Fetching {len(unique)} specs from {len(SUPPORTED_SERVICES)} supported services...\n")

    pulled = []
    skipped = []
    for base_url, name in unique.items():
        spec = fetch_swagger(base_url)
        if spec is None:
            skipped.append(name)
            continue
        path = schemas_dir / f"{name}.json"
        path.write_text(json.dumps(spec, indent=2))
        pulled.append({
            'name': name,
            'base_url': base_url,
            'services': services_for_url(services, base_url),
        })

    pulled.sort(key=lambda e: e['name'])
    skipped.sort()

    print(f"Pulled {len(pulled)} spec(s) to {schemas_dir}:")
    for entry in pulled:
        print(f"  OK   {entry['name']:12s}  {entry['base_url']}")

    if skipped:
        print(f"\nSkipped {len(skipped)} spec(s) (no valid swagger endpoint):")
        for name in skipped:
            print(f"  SKIP {name}")

    template_path = project_root / 'docs/pull-openapi-json-template.md'
    write_readme(template_path, schemas_dir / 'README.md', pulled)

    total_size = sum((schemas_dir / f"{e['name']}.json").stat().st_size for e in pulled)
    print(f"\nTotal: {len(pulled)} spec(s), {total_size:,} bytes")

if __name__ == '__main__':
    main()
