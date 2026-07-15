FROM sirblondiedk/hadocs:dev

ARG BUILD_VERSION
ARG BUILD_ARCH

LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

COPY run.sh /run.sh

RUN chmod a+x /run.sh

ENTRYPOINT []
CMD ["/run.sh"]