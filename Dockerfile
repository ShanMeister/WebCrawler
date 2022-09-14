FROM python:3.9.12-slim-bullseye as base
FROM base as builder
COPY requirements.txt /requirements.txt
RUN pip3 install --user -r /requirements.txt

FROM base
# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY . /root
WORKDIR /root

# update PATH environment variable
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080
CMD ["bash","-x","/root/start_to_crawl.sh", ">> /root/output/log.txt"]
