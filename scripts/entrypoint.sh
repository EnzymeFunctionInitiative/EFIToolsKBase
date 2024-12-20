#!/bin/bash

. /kb/deployment/user-env.sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "init" ] ; then
  echo "Initialize module"
  remote_base="https://efi.igb.illinois.edu/downloads/databases/latest"

  DIR=/data

  CURL_RETURN_CODE=0
  file="efidata.tar.gz"
  echo "curl -o $DIR/$file https://efi.igb.illinois.edu/downloads/sample_data/old/kb_test_all/kb_test_all.tar.gz"
  curl -o $DIR/$file https://efi.igb.illinois.edu/downloads/sample_data/old/kb_test_all/kb_test_all.tar.gz
  if [ $CURL_RETURN_CODE -eq 0 ] ; then
    tar xzf $DIR/$file -C $DIR
  fi
  ls $DIR

  CURL_RETURN_CODE=0
  file="large_gnd.sqlite"
  echo "curl -o $DIR/$file https://efi.igb.illinois.edu/downloads/large_gnd.sqlite"
  curl -o $DIR/$file https://efi.igb.illinois.edu/downloads/large_gnd.sqlite
  ls $DIR

  echo "Skipping database download"
  #file="blastdb.tar.gz"
  #echo "Downloading database $file"
  #python scripts/download_file.py --remote-dir $remote_base/blastdb --remote-file $file --local-dir $DIR/temp_$file --local-file $DIR/$file
  #rm -rf $DIR/temp_$file
  #tar xzf $DIR/$file -C $DIR
  #rm $DIR/$file

  #file="diamonddb.tar.gz"
  #echo "Downloading database $file"
  #python scripts/download_file.py --remote-dir $remote_base/diamonddb --remote-file $file --local-dir $DIR/temp_$file --local-file $DIR/$file
  #rm -rf $DIR/temp_$file
  #tar xzf $DIR/$file -C $DIR
  #rm $DIR/$file

  #file="efi_db.sqlite.gz"
  #echo "Downloading database $file"
  #python scripts/download_file.py --remote-dir $remote_base/efi_db --remote-file $file --local-dir $DIR/temp_$file --local-file $DIR/$file
  #rm -rf $DIR/temp_$file
  #gunzip $DIR/$file

  touch $DIR/__READY__
elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  make compile
else
  echo Unknown
fi

