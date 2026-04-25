FROM odoo:18

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
        "fastembed>=0.5,<0.7" \
        "pgvector>=0.3,<1.0"

ENV FASTEMBED_CACHE_DIR=/var/lib/odoo/.fastembed_cache
RUN mkdir -p $FASTEMBED_CACHE_DIR && chown -R odoo:odoo /var/lib/odoo

USER odoo
