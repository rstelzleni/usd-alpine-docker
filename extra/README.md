# Extra

This is an image where I add extra stuff that isn't part of base USD.
Use at your own risk, even more than normal :D

The current version is the same as usd-25.05.01, but with a new class
I wrote to redirect USD's logging into the python logging system.
See the branch pulled in the Dockerfile for details.

The short version is with this image you can do:

```python
from pxr import UsdUtils
delegate = UsdUtils.PythonLoggingDiagnosticDelegate()
```

Then as long as that exists USD messages will be logged in python.
See python help for more details.
