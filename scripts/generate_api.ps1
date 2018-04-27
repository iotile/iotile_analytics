# It is very important that this script runs in python 3
# since it calls importlib.import_module which does not 
# properly work on python 2.  In particular it gets confused
# with directly importing submodules and thinks some of iotile_analytics.offline
# is actually part of pytables.

workspace\env3\Scripts\Activate.ps1

Remove-Item doc\api -Recurse -ErrorAction Ignore

python scripts/better_apidoc.py -o doc\api .\iotile_analytics_core\iotile_analytics -f -e -t doc/_template
python scripts/better_apidoc.py -o doc\api .\iotile_analytics_interactive\iotile_analytics -f -e -t doc/_template
python scripts/better_apidoc.py -o doc\api .\iotile_analytics_offline\iotile_analytics -f -e -t doc/_template

rm doc\api\modules.rst
rm doc\api\iotile_analytics.rst
