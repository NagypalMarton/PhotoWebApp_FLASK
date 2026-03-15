FROM registry.access.redhat.com/ubi9/ubi-minimal

ENV MYSQL_VERSION=8.0 \
	MYSQL_USER=mysql \
	MYSQL_UID=1001 \
	MYSQL_GID=0 \
	MYSQL_DATADIR=/var/lib/mysql

# Install MySQL and dependencies
RUN microdnf install -y mysql-server && \
	microdnf clean all && \
	mkdir -p ${MYSQL_DATADIR} && \
	chown -R ${MYSQL_UID}:${MYSQL_GID} ${MYSQL_DATADIR} && \
	chmod -R g+rwX ${MYSQL_DATADIR}

USER ${MYSQL_UID}

EXPOSE 3306

VOLUME ["${MYSQL_DATADIR}"]

ENTRYPOINT ["mysqld"]
