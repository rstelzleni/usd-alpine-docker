# The Odyssey

An epic poem about getting this to build the first time, in free verse,
mostly written as I worked.

A fresh eyed beginner, I thought this would take a few hours

## Day One

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

installing linux-headers fixed it

Next issue:

```
error: declaration of 'tbb::task& tbb::internal::task_prefix::task()' changes meaning of 'task'
```

This is in TBB.

Appears to be a legit compiler error with gcc 13. Fix in another project is here

https://github.com/bambulab/BambuStudio/pull/1882

Alpine uses gcc 13.2, and USD requires an older TBB. Looks like on linux it
uses v2020.3, and that's the newest supported version on any of the other
platforms as well. It seems that TBB `task` was removed in OneTBB v2021.01, so
I'm not positive if there's a v2020 version that fixes this gcc 13 build error.

The Alpine package manager does offer a prebuilt onetbb v2021.11, but I suspect
that's too new to work with USD. Especially since the `task` type has been
removed in that version.

Reviewed recent release notes and read up on this _long_ github issue

https://github.com/PixarAnimationStudios/OpenUSD/issues/1471

Recent TBB is not explicitly supported yet, but it looks like some of the
deprecated modules have been trimmed out or replaced with std alternatives. It
may be possible to build with the apk's onetbb, or to compile with a newer tbb
version using build_usd.py

I'm torn between switching to a cmake build so I can explicitly specify
dependencies, and trying to patch the build_usd.py script to choose a tbb that
may build with gcc13.

Taking a break

## Later That Night...

Resuming. If I try to build with Cmake directly and use the alpine boost
(1.82.0) and the alpine tbb (2021.11.0) boost seems to work but tbb isn't found
by cmake. This version of FindTBB.cmake looks for a header called
`tbb/tbb_stddef.h` and that file doesn't exist in the newer tbb libs. The
advice online seems to be to stop using the old FindTBB and rely instead on the
cmake files that ship with onetbb. I suspect this will not be the last hurdle
with using tbb 2021, so now we have two solutions for tbb:

- Use the supported tbb version, 2020.3 by compiling ourselves. Breaks because it isn't updated for gcc 13
- Use the alpine tbb version, 2021.11. Breaks because USD isn't updated for the new api

One way to thread this needle would be to get the 2020.3 source, patch it to
build in gcc 13, build our own version and then build USD using cmake directly
instead of build_usd.py. I guess that's what I'll try next.

TBB 2020.3 seems to need 2 changes to build under gcc 13. A namespace is
missing on a task object in one header, and a feature for hooking malloc needs
to be disabled, because it relies on a mallinfo struct that is only
implementedin glibc. Our musl libc doesn't have it. This can be disabled by
setting a value in a header.

Oh, also, the macro __GLIBC_PREREQ is not defined, so checks that call it as a
function fail in the preprocessor, even if the check would be short-circuited
by a `defined` check. So, 3 changes

Once that's done I get a successful build, and the TBB tests pass in the
container. One note about the tests, I do get this warning:

```
./test_concurrent_vector.exe  
Warning: not much concurrency in TestConcurrentGrowBy (37 inversions)
done
```

The rest of the tests pass without complaint, so the next step is to automate
this build in the dockerfile. I'll do that with a couple patch files we'll
apply to the downloaded TBB files. Then in the docker container we'll copy the
TBB artifacts into a vendored dependencies folder for USD and move on.

Breaking, end of day one

Wait, one more thing first. Tried a first USD build and I get past the
configure step. First failure hit was in pxr/base/arch/assumptions.cpp. It
wants to figure out the L1 cache size using a non-POSIX glibc extension called
_SC_LEVEL1_DCACHE_LINESIZE. This is not available in Alpine linux, and the
information in general also seems to be hard to find. For instance, in
/proc/cpuinfo almost all fields are null inside the docker container.

I found the patch linked below where the author worked around this by setting a
"reasonable value" of 64, so I'm doing the same.

https://git.alpinelinux.org/aports/commit/?id=cd359b79b1c5cb21a1edf5162b2943f9dc57f18d

This gets me to my next arch error, but that's a problem for tomorrow. Sleeping
now

## A Fresh New Day

Notes:
cmake configuring generates a lot of files, do it in a build dir maybe should
set the install dir so its easier to copy

Changed last time:
```
pxr/base/arch/assumptions.cpp
@@ -51,7 +51,7 @@ static size_t
 Arch_ObtainCacheLineSize()
 {
 #if defined(ARCH_OS_LINUX)
-    return sysconf(_SC_LEVEL1_DCACHE_LINESIZE);
+    return 64; //sysconf(_SC_LEVEL1_DCACHE_LINESIZE);

pxr/base/arch/errno.cpp
@@ -43,7 +43,7 @@ ArchStrerror(int errorCode)
 {
     char msg_buf[256];
    
-#if defined(_GNU_SOURCE)
+#if defined(FALSE) // _GNU_SOURCE)

pxr/base/arch/stackTrace.cpp
@@ -664,7 +664,7 @@ nonLockingLinux__execve (const char *file,
 static int
 nonLockingExecv(const char *path, char *const argv[])
 {
-#if defined(ARCH_OS_LINUX)
+#if defined(FALSE) //ARCH_OS_LINUX)

--- a/pxr/base/tf/atomicRenameUtil.cpp
+++ b/pxr/base/tf/atomicRenameUtil.cpp
@@ -89,6 +89,7 @@ Tf_AtomicRenameFileOver(std::string const &srcFileName,
     // 0600. When renaming our temporary file into place, we either want the
     // permissions to match that of an existing target file, or to be created
     // with default permissions modulo umask.
+# define DEFFILEMODE (S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP|S_IROTH|S_IWOTH)

--- a/pxr/base/tf/testenv/atomicOfstreamWrapper.cpp
+++ b/pxr/base/tf/testenv/atomicOfstreamWrapper.cpp
@@ -40,6 +40,10 @@
 #include <sys/stat.h>
 #include <fcntl.h>
 
+# define ACCESSPERMS (S_IRWXU|S_IRWXG|S_IRWXO) /* 0777 */
+# define ALLPERMS (S_ISUID|S_ISGID|S_ISVTX|S_IRWXU|S_IRWXG|S_IRWXO)/* 07777 */
+# define DEFFILEMODE (S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP|S_IROTH|S_IWOTH)/* 0666*/
+

--- a/pxr/base/tf/testenv/safeOutputFile.cpp
+++ b/pxr/base/tf/testenv/safeOutputFile.cpp
@@ -40,6 +40,11 @@
 #include <sys/stat.h>
 #include <fcntl.h>
 
+# define ACCESSPERMS (S_IRWXU|S_IRWXG|S_IRWXO) /* 0777 */
+# define ALLPERMS (S_ISUID|S_ISGID|S_ISVTX|S_IRWXU|S_IRWXG|S_IRWXO)/* 07777 */
+# define DEFFILEMODE (S_IRUSR|S_IWUSR|S_IRGRP|S_IWGRP|S_IROTH|S_IWOTH)/* 0666*/
+
```

With those changes 95% passing tests! so close

The following tests FAILED:
	 8 - testArchStackTrace (Failed)
	11 - testArchTiming (Failed)
	15 - TfAtomicOfstreamWrapper (Failed)
	30 - TfFileUtils (Failed)
	35 - TfHash (Failed)
	49 - TfRWMutexes (Failed)
	55 - TfSafeOutputFile (Failed)
	56 - TfScopeDescription (Failed)
	65 - TfStopwatch (Failed)
	126 - testTraceData (Failed)
	128 - testTraceMacros (Failed)
	129 - testTraceThreading (Failed)


	 8 - testArchStackTrace (Failed)
This is looking for a stack frame with "main" in it, but it gets only
one frame with the calling function in it:
- #0   0x0000ffffb166a5a0 in pxrInternal_v0_24__pxrReserved__::ArchGetStackFrames(unsigned long, unsigned long, unsigned long*)+0x40

The change made to stackTrace is just to use the standard execv instead of one
that doesn't exist in musl libc. That doesn't seem like the culprit. Maybe try
a rebuild after installing libunwind and libunwind-dev

	11 - testArchTiming (Failed)
Could be about rdtscp? It definitely seems to be crashing in one of the 
Arch tick getting functions

## Took a Break, Picked Up Day 3 in the Airport

X	15 - TfAtomicOfstreamWrapper (Failed)
Failing this axiom on line 67
TF_AXIOM(!TfAtomicOfstreamWrapper("/var/run/testTf_file_").Open());
Apparently it should exercise insufficient permission to create a file. This
may be happening because we're running as root. Commenting this test and
a second that edits /etc/passwd out results in a passing test.

X	30 - TfFileUtils (Failed)
Same issue as above, we are root, so everything is writable
Fixed by commenting out checks

	35 - TfHash (Failed)
Looks like a crash while doing some bit twiddling. It's using a TfStopwatch, so
may be related to the testArchTiming crashes

	49 - TfRWMutexes (Failed)
Also may be stopwatch

X	55 - TfSafeOutputFile (Failed)
Root permissions issue. Commenting out tests for unwritable folders fixes

    56 - TfScopeDescription (Failed)
	65 - TfStopwatch (Failed)
Uses stopwatch, looks like that crash

	126 - testTraceData (Failed)
	128 - testTraceMacros (Failed)
	129 - testTraceThreading (Failed)
looks like timing failure, exit code 139

## Day 4

Resuming after doing that test failure checking in the airport

I think the next step is to build a new container with the fixes mentioned
above, but using a new branch of the USD source. Starting on that now.

At this point I translated my in-container build instructions and changes into
a USD branch and commands in the dockerfile and killed my dev container.

Mostly working! But binaries too big. also, it's almost 3 am.

Here's a command line

```
cd /src/USD-build/pxr/base/gf && /usr/bin/c++ -DBOOST_NO_CXX98_FUNCTION_BASE -DBOOST_PYTHON_NO_PY_SIGNATURES -DGLX_GLXEXT_PROTOTYPES -DGL_GLEXT_PROTOTYPES -DMFB_ALT_PACKAGE_NAME=gf -DMFB_PACKAGE_MODULE=Gf -DMFB_PACKAGE_NAME=gf -D_gf_EXPORTS -I/src/USD-build/include -isystem /usr/include/python3.11 -isystem /opt/vendored/include -Wall -Wformat-security -pthread -Wno-deprecated -Wno-deprecated-declarations -Wno-unused-local-typedefs -Wno-maybe-uninitialized -Os -s -O3 -DNDEBUG -std=c++17 -fPIC -MD -MT pxr/base/gf/CMakeFiles/_gf.dir/wrapLimits.cpp.o -MF CMakeFiles/_gf.dir/wrapLimits.cpp.o.d -o CMakeFiles/_gf.dir/wrapLimits.cpp.o -c /src/USD/pxr/base/gf/wrapLimits.cpp
```

Why do I get -Os and -O3?

## Day 5

Down to 8 test failures:
	 
     8 - testArchStackTrace (Failed)
Looks like the same failure, I don't think including libunwind fixed this.

	15 - TfAtomicOfstreamWrapper (Failed)
	30 - TfFileUtils (Failed)
	55 - TfSafeOutputFile (Failed)
These all appear to be testing for writability, adding a "is root user" function
to avoid these.

	159 - testTsSplineAPI (Failed)
Interesting. Got a derivative of 1 when expecting 2. I wonder if this is a real
failure independent of this build.

	512 - testUsdSkelBakeSkinning (Failed)
/src/USD-build/Testing/Failed-Diffs/2024-04-16T19.26.26/testUsdSkelBakeSkinning
Need to check this once I'm done triaging failures. 

Checked, differences all look like maybe floating point drift? Hard to say, the
test outputs a lot of text. Definitely looks like printf floating precision
issues. The files are compared with regular diff with no tolerance.

	573 - testUsdUtilsStitchClips (Failed)
	627 - testUsdEditFilePermissions1 (Failed)
Checking permissions, avoid running as root

Fixes in, binaries shrunk as much as is reasonable. Cleaned up the Dockerfile
and committing.

## Day 6

Made the dockerhub repo and figured out how to build for arm and amd. Pushed
the first images, and sailed my ship home.
