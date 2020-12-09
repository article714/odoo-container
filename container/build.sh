#!/bin/bash

#set -x

apt-get update

# Generate French locales
localedef -i fr_FR -c -f UTF-8 -A /usr/share/locale/locale.alias fr_FR.UTF-8

export LANG=en_US.utf8

# Install basic needed packages
LC_ALL=C DEBIAN_FRONTEND=noninteractive apt-get install -qy --no-install-recommends runit rsyslog logrotate

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
apt-get update
apt-get upgrade -yq

apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    dialog \
    dirmngr \
    fonts-noto-cjk \
    git \
    gnupg \
    nodejs \
    node-less \
    npm \
    python3-configobj \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-pyldap \
    python3-qrcode \
    python3-renderpm \
    python3-setuptools \
    python3-unidecode \
    python3-vobject \
    python3-watchdog \
    python3-wheel \
    redis software-properties-common \
    python3-redis \
    wget \
    wkhtmltopdf \
    xz-utils

# install latest postgresql-client
echo 'deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main' >etc/apt/sources.list.d/pgdg.list
export GNUPGHOME="$(mktemp -d)"
repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8'
gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}"
gpg --armor --export "${repokey}" | apt-key add -
gpgconf --kill all
rm -rf "$GNUPGHOME"
apt-get update
apt-get install -y postgresql-client
rm -rf /var/lib/apt/lists/*

# update wkhtmltopdf (issues with reports)
apt-get remove -qy wkhtmltopdf
apt-get install -qy libfontenc1 xfonts-75dpi xfonts-base xfonts-encodings xfonts-utils
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb
dpkg --force-depends -i wkhtmltox_0.12.6-1.buster_amd64.deb
apt-get -y install -f --no-install-recommends
apt --fix-broken install
rm -f wkhtmltox_0.12.6-1.buster_amd64.deb

# Install rtlcss
npm install -g rtlcss

# Install pip dependencies
pip3 install num2words phonenumbers xlwt xlrd

# ODOO user should have a > 1000 gid to ease uid/gid mapping in docker
addgroup --gid 1001 odoo

adduser --system --home /var/lib/odoo --gid 1001 --uid 1001 --quiet odoo
adduser odoo syslog

chown -R odoo. /home/odoo
chmod -R 770 /home/odoo

# Install Odoo
export ODOO_VERSION=11.0
export ODOO_RELEASE=latest

curl -o odoo.deb -sSL http://nightly.odoo.com/${ODOO_VERSION}/nightly/deb/odoo_${ODOO_VERSION}.${ODOO_RELEASE}_all.deb
dpkg --force-depends -i odoo.deb
apt-get update
apt-get -y install -f --no-install-recommends
rm -rf /var/lib/apt/lists/* odoo.deb

# install Odoo dependencies

mkdir -p /home/odoo/addons
chown -R odoo. /home/odoo/addons
chmod ug+s /home/odoo/addons
cp /container/config/odoo/modules_dependencies.txt /home/odoo/addons

cd /home/odoo/addons
python3 /container/tools/clone_dependencies.py /home/odoo/addons ${ODOO_VERSION}
cd /

# Copy Odoo configuration file
chgrp -R odoo /container/config/odoo

# Mount /var/lib/odoo to allow restoring filestore and /mnt/extra-addons for users addons
mkdir -p /mnt/extra-addons
chown -R odoo /mnt/extra-addons
chmog g+s /var/lib/odoo
mkdir -p /var/lib/odoo
chown -R odoo /var/lib/odoo
chmog ug+s /var/lib/odoo

#--
# Cleaning

apt-get -yq clean
apt-get -yq autoremove
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/ci
rm -f tmp/*_dependencies.txt
