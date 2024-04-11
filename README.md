# USD Alpine Docker

USD builds in alpine docker, for making slim docker containers with USD support.

## Log

I should probably consolidate this into a separate document

### First try

My first attempt at this was to just run the build_usd.py script and see what
failed. I used a trimmed down command line:

```
python3 build_scripts/build_usd.py \
    --build-variant=release \
    --src=/src/deps \
    --inst=/opt/USD-deps \
    --no-tests \
    --no-examples \
    --no-tutorials \
    --no-imaging \
    /opt/USD
```

The first error encountered was in building boost. There are quite a few of these:

```
 In file included from ./boost/python/detail/prefix.hpp:13,
                  from ./boost/python/object_operators.hpp:8,
                  from libs/python/src/object_operators.cpp:6:
 ./boost/python/detail/wrap_python.hpp:82:10: fatal error: patchlevel.h: No such file or directory
    82 | #include <patchlevel.h>
       |          ^~~~~~~~~~~~~~
 compilation terminated.
```

This was fixed with installing the python-dev package.

Next issue: 

```
 ERROR: Failed to run './b2 --prefix="/opt/USD-deps" --build-dir="/opt/USD/build" -j10 address-model=64 link=shared runtime-link=shared threading=multi variant=release --with-atomic --with-regex --with-python --user-config=python-config.jam install'
 See /src/deps/boost_1_82_0/log.txt for more details.
```

Found this in a sea of deprecation warnings

```
fatal error: linux/futex.h: No such file or directory
```

installing linux-headers fixed

Next issue:

```
error: declaration of 'tbb::task& tbb::internal::task_prefix::task()' changes meaning of 'task'
```

This is in TBB.

Appears to be a legit compiler error with gcc 13. Fix in another project is here

https://github.com/bambulab/BambuStudio/pull/1882

Alpine uses gcc 13.2, and USD requires an older TBB from before the OneTBB version,
looks like on linux it uses v2020.3, and that's the newest supported version on any
of the other platforms as well. It seems that TBB task was removed in OneTBB v2021.01,
so I'm not positive if there's a 2020 version that fixes this gcc 13 build error.

The Alpine package manager does offer a prebuilt onetbb v2021.11, but I suspect that's
too new to work with USD. Especially since the task type has been removed in that 
version.

Reviewed recent release notes and read up on this _long_ github issue

https://github.com/PixarAnimationStudios/OpenUSD/issues/1471

OneTBB is not explicitly supported yet, but it looks like some of the deprecated
modules have been trimmed out or replaced with std alternatives. It may be possible
to build with the apk's onetbb, or to compile with a newer tbb version using build_usd.py

I'm torn between switching to a cmake build so I can explicitly specify dependencies,
and trying to patch the build_usd.py script to choose a tbb that may build with gcc13.

Taking a break

Resuming. If I try to build with Cmake directly and use the alpine boost (1.82.0) and
the alpine tbb (2021.11.0) boost seems to work but tbb isn't found by cmake. This version
of FindTBB.cmake looks for a header called `tbb/tbb_stddef.h` and that file doesn't exist
in the newer tbb libs. The advice online seems to be to stop using the old FindTBB and
rely instead on the cmake files that ship with onetbb. I suspect this will not be the
last hurdle with using tbb 2021, so now we have two non-starter solutions for tbb:

- Use the supported tbb version, 2020.3 by compiling ourselves. Breaks because it isn't updated for gcc 13
- Use the alpine tbb version, 2021.11. Breaks because USD isn't updated for the new api

One way to thread this needle would be to get the 2020.3 source, patch it to build in 
gcc 13, build our own version and then build USD using cmake directly instead of build_usd.py.
I guess that's what I'll try next.

TBB 2020.3 seems to need 2 changes to build under gcc 13. A namespace is missing on a
task object in one header, and a feature for hooking malloc needs to be disabled, because
it relies on a mallinfo struct that is only implementedin glibc. Our musl libc doesn't
have it. This can be disabled by setting a value in a header.

Oh, also, the macro __GLIBC_PREREQ is not defined, so checks that call it as a function
fail in the preprocessor, even if the check would be short-circuited by a defined check.
So 3 changes

Once that's done I get a successful build, and the TBB tests pass in the container. One
note about the tests, I do get this warning:

```
./test_concurrent_vector.exe  
Warning: not much concurrency in TestConcurrentGrowBy (37 inversions)
done
```

The rest of the tests pass without complaint, so the next step is to automate this
build in the dockerfile. I'll do that with a couple patch files we'll apply to the
downloaded TBB files. Then in the docker container we'll copy the TBB artifacts into
a vendored dependencies folder for USD and move on.


