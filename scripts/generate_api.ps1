workspace\env\Scripts\activate.ps1

Remove-Item doc\api -Recurse -ErrorAction Ignore

better-apidoc -o doc\api .\iotile_analytics_core\iotile_analytics -f -e -t doc/_template
better-apidoc -o doc\api .\iotile_analytics_interactive\iotile_analytics -f -e -t doc/_template
better-apidoc -o doc\api .\iotile_analytics_offline\iotile_analytics -f -e -t doc/_template

rm doc\api\modules.rst
rm doc\api\iotile_analytics.rst
