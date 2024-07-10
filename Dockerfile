FROM kbase/sdkpython:3.8.0

# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# install zip/unzip for duckdb and nextflow
RUN apt update && apt install -y zip unzip cpanminus libdbd-mysql-perl zip fortune cowsay

# install blastall
RUN curl -o /opt/blast-2.2.26.tar.gz https://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz; \
    tar xzf /opt/blast-2.2.26.tar.gz -C /opt; \
    rm /opt/blast-2.2.26.tar.gz
ENV PATH="${PATH}:/opt/blast-2.2.26/bin"

# install duckdb
RUN mkdir /opt/duckdb; \
    curl -L -o /opt/duckdb/duckdb.zip https://github.com/duckdb/duckdb/releases/download/v1.0.0/duckdb_cli-linux-amd64.zip && \
    unzip /opt/duckdb/duckdb.zip -d /opt/duckdb && \
    rm /opt/duckdb/duckdb.zip
ENV PATH="${PATH}:/opt/duckdb"

# install nextflow
RUN curl -s https://get.sdkman.io | bash && \
    echo 'source /root/.sdkman/bin/sdkman-init.sh && sdk install java 17.0.10-tem' | bash
RUN curl -o /opt/install_nextflow.sh https://get.nextflow.io && chmod +x /opt/install_nextflow.sh && \
    echo 'source /root/.sdkman/bin/sdkman-init.sh && /opt/install_nextflow.sh' | bash && \
    mv /opt/install_nextflow.sh /usr/bin/nextflow

# install EST scripts
RUN git clone https://github.com/EnzymeFunctionInitiative/EST.git && \
    cd EST && \
    git checkout nextflow-test && \
    cpanm --installdeps /EST/

# install efi.config
COPY efi.config /EST

# create conda env for nextflow
RUN conda env create -f /EST/env.yml

# -----------------------------------------
WORKDIR /kb/module
COPY ./requirements.txt /kb/module/requirements.txt
ENV PIP_PROGRESS_BAR=off
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -e git+https://github.com/kbase-sfa-2021/sfa.git#egg=base

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
