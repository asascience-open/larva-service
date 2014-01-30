#!bash

function download_extract_compile_install {
    # Download
    mkdir -p "$2"
    cd "$2"
    if $3 ; then
        wget "$1"
    fi

    # Extract
    FLNAME=${1##*/}
    tar zxf "$FLNAME"

    # Configure
    mkdir -p "$4"
    PREFIX=$(basename ${FLNAME##*/} .tar.gz)
    cd "$2/$PREFIX"
    ./configure --prefix="$4/$PREFIX" $5
    echo "Sleeping for 10 seconds, check configure output for errors"
    sleep 10

    # Compile
    make -j $6
    echo "Sleeping for 10 seconds, check compile output for errors"
    sleep 10

    # Install
    mkdir -p "$4"
    rm -rf "$4/$PREFIX"
    make install
}

INSTALL_PATH=/opt
DOWNLOAD_PATH=/opt/src
DO_DOWNLOAD=true
THREADS=10

HDF5_URL="http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.12.tar.gz"
HDF5_PREFIX=$(basename ${HDF5_URL##*/} .tar.gz)
CONFIG_OPTIONS=""
download_extract_compile_install "$HDF5_URL" "$DOWNLOAD_PATH" "$DO_DOWNLOAD" "$INSTALL_PATH" "$CONFIG_OPTIONS" "$THREADS"

NETCDF4_URL="ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.3.1.tar.gz"
export LDFLAGS="-L/opt/$HDF5_PREFIX/lib"
export CPPFLAGS="-I/opt/$HDF5_PREFIX/include"
CONFIG_OPTIONS="--enable-netcdf4 --enable-mmap"
download_extract_compile_install "$NETCDF4_URL" "$DOWNLOAD_PATH" "$DO_DOWNLOAD" "$INSTALL_PATH" "$CONFIG_OPTIONS" "$THREADS"
