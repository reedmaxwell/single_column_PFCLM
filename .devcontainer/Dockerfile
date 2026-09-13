# ParFlow v3.15.0 (release cited in the manuscripts) + Python stack for the
# notebooks.  The base image sets PARFLOW_DIR=/usr/opt/parflow and
# container-friendly MPI flags (--allow-run-as-root, oversubscribe).
FROM parflow/parflow:version-3.15.0

RUN pip3 install --no-cache-dir \
    pftools \
    subsettools \
    hf_hydrodata \
    xarray \
    netcdf4 \
    numpy \
    pandas \
    matplotlib \
    bokeh \
    jupyter \
    ipykernel
