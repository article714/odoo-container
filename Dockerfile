FROM article714/debian-based-container:latest
LABEL maintainer="C. Guychard <christophe@article714.org>"

# Container tooling

COPY container /container

ENV PATH=/usr/local/bin:${PATH}

# Build container

RUN /container/build.sh

# Expose Odoo services
EXPOSE 8069 8071

# Set the default config file
ENV ODOO_RC /container/config/odoo/odoo.conf

