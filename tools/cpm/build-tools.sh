
__dir__=$(cd $(dirname ${BASH_SOURCE[0]}); pwd )
__script__=$(cd $__dir__/../../cerbero/tools ; pwd )/cpm.py
echo $__script__
rootd='d:/github.com/cerbero/build/build-tools'
python $__script__ pack --name build-tools --prefix gstreamer --version 1.12.3 --platform windows --arch x86_64 --type runtime --root-dir $rootd