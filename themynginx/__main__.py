# -*- coding=utf-8 -*-
import logging
import os
import subprocess
import sys

from jinja2 import Template
import oyaml

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        config = oyaml.load(f)

    with open(os.path.join(os.path.dirname(__file__), "site.conf.jinja2")) as f:
        template = Template(f.read())

    sites_enabled = "/etc/nginx/sites-enabled"
    for f in os.listdir(sites_enabled):
        os.unlink(os.path.join(sites_enabled, f))

    for i, (server_name, config) in enumerate(config.items()):
        letsencrypt_cert_dir = os.path.join("/etc/letsencrypt/live", server_name)

        letsencrypt_webroot_dir = os.path.join("/var/lib/letsencrypt", server_name)
        os.makedirs(letsencrypt_webroot_dir, exist_ok=True)

        if config.get("letsencrypt"):
            subprocess.check_call([
                "docker", "run",
                "-v", "/var/lib/letsencrypt:/var/lib/letsencrypt",
                "-v", "/etc/letsencrypt:/etc/letsencrypt",
                "-it",
                "--rm",
                "deliverous/certbot:0.14.x",

                "certonly",
                "--non-interactive",
                "--agree-tos",
                "--expand",
                "--email", "letsencrypt@%s" % server_name,
                "--webroot", "--webroot-path", letsencrypt_webroot_dir,
                "-d", server_name,
            ])

        output = template.render(
            default=i == 0,
            server_name=server_name,
            letsencrypt_cert_dir=letsencrypt_cert_dir,
            letsencrypt_webroot_dir=letsencrypt_webroot_dir,
            has_letsencrypt_cert=os.path.exists(os.path.join(letsencrypt_cert_dir, "fullchain.pem")),
            **config
        )

        with open(os.path.join(sites_enabled, server_name), "w") as f:
            f.write(output)
