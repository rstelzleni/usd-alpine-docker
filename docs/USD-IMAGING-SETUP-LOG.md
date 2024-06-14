# Setting up a usd imaging enabled build

Starting this on May 7th, 2024. The goal is to make a base image that could
be used to get headless renders.

## Planning

Thinking this through, may main motivation could be described in two parts,

1) Render a static image from a docker command
2) Render a stream of images for a viewport from a docker server

I'd like to support this on arm64 and amd64 hosts.

GPU acceleration would be great, but I don't want it to be a deal breaker, I'd
like some way to get an image on any machine, or to use a no-gpu server as a
render server.

Material support is an issue. What material libraries could be supported? 
Should this be preview surface only? Is MaterialX the second thing to support?

Y = Yes
M = Maybe

| Option         | static | stream | amd64 | arm64 | prev surf | MatX | GPU | Mac GPU | alpine | perf | quality | Notes |
| :-----------   | :----: | :----: | :---: | :---: | :-------: | :--: | :-: | :-----: | :----: | :--- | :------ | :---- |
| Headless GL    |   Y    |   Y    |   Y   |   Y   |    Y      |  M   |     |         |   Y    | Poor | Poor    | Mesa w/Gallium LLVMpipe, vfb |
| GPU GL         |   Y    |   Y    |   Y   |       |    Y      |  M   |  Y  |         |   Y    | Good | Poor    | Using docker GPU passthrough |
| threejs custom |        | client |   Y   |   Y   |    Y      |  M   |  Y  |    Y    |   Y    | Good | Poor    | server streams predigested content to threejs |
| embree         |   Y    |        |   Y   |   Y   |    Y      |  M   |     |         |   Y    | Poor | Good    | alpine has an embree package |
| prman          |   Y    |        |   Y   |       |    Y      |  Y   |     |         |        | Ok   | Good    | I don't think prman is dockerizable easily, and xpu might be tough to enable |
| moonray        |   Y    |        |   Y   |   M   |    Y      |      |     |         |        | Poor | Good    | No alpine version I can find, but does look dockerizable |

There are really two categories, real time vs high quality. 

### Real Time Render Servers

I've listed a few, my initial thoughts are that headless GL will be easiest to
bootstrap and prove out the idea, GPU accelerated on the server I'm rejecting in my
mind at the moment because I'd really need a build or version per target platform
I want to support. This is interesting, but I think it would be a whole big project
on its own and I'd like to move fast if possible.

The threejs idea is really, write a render delegate that outputs content pre-digested
for threejs, maybe including using MaterialX's javascript bindings to generate shaders.
I like this idea and would like to give it a try, but it might come later. It has the
advantage that the GPU support is offloaded to the browser that runs the code.

### High Quality Render Servers

These are more like offline renderers. You get higher quality, but at the cost of time,
and they're not fast enough for realtime feedback. That has a place, and I'd like to make
something like this. 

The path of least resistance might be embree. There's already a render delegate for it,
and there is an alpine linux package. The package uses onetbb, so that might be an issue,
but I'll burn that bridge when I come to it.

My second favorite option here is moonray. It doesn't need license servers or anything, 
and the documentation indicates that they've used docker containers with it, so it
ought to be packagable. There's no alpine build, but it would be interesting to try.
Their packages come in at over 600 MB, but they're not removing build files, and they're
building on rocky or centos distros that are bigger to begin with. It doesn't support
MaterialX though, so it'd be preview surface only unless I add matx support.

### Planning Wrap Up

I think this suggests a few things to try first.

* Get a realtime renderer working with software GL
* Get a high quality renderer working with embree package

Then, if all goes well or we hit roadblocks:

* Try making a realtime version that returns digested content to threejs
* Try packaging moonray in a smaller package and using for a render server

There are two wildcards here. Alembic and MaterialX. There is an alpine alembic package,
but I might wait to add that and start with the no-imaging version. There is no alpine
materialx package, so that might require a custom build. I think I'll wait on that, and
try to get things working with preview surface only for the moment.

## Getting started

First step, get an alpine docker container with software openGL that can render
images using `usdrecord`

Gallium LLVMpipe appears to be x86 and ppc64 only, no arm. (turns out this is false)

End day one. I have all but 30 tests passing in a headless container. 3 or so of those
are not imaging related, but all the UsdRecord related tests fail. These seem like
issues with system configuration or at least of Usd's detection of correct displays.
To be continued

## Day Two

I don't have as much time today. I started by experimenting with getting a more complete
x11 environment set up. I've experimented with adding xterm so there is a startup program,
and with adding fluxbox to get a windowing system to make Qt more happy. So far I'm still
stuck with the same test failures, but some failure reasons have been eliminated and
others are becoming more clear.

I'm starting things like this at the moment:
```
xinit -- /usr/bin/Xvfb :0 -screen 0 1024x768x24
fluxbox
```

I'm not positive fluxbox is needed.

One class of errors I'm getting looks like this

```
qt.qpa.xcb: could not connect to display
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.
```

In this caset it seems to be because the test executable is not finding the right display.
If, for instance, I start on display :99 and `export DISPLAY=:99` then I get past these
Qt errors. It does not seem to be about installing libxcb-cursor (which on alipine is
xcb-util-cursor). I'm not sure if defining and setting a DISPLAY is the right fix, but
it does bring me to the next error.

```
Warning: in SdfPath at line 144 of /src/USD/pxr/usd/sdf/path.cpp -- Ill-formed SdfPath <>: :1:0(0): parse error matching pxrInternal_v0_24_
Warning: in HgiGLMeetsMinimumRequirements at line 137 of /src/USD/pxr/imaging/hgiGL/diagnostic.cpp -- XXXXX GL VERSION IS OpenGL ES 3.2 Mesa 23.3.6
                                                                                                                                           
Warning: in operator() at line 71 of /src/USD/pxr/imaging/hgiGL/hgi.cpp -- HgiGL minimum OpenGL requirements not met. Please ensure that Op
Traceback (most recent call last):                                                                                                         
  File "/opt/USD/bin/usdrecord", line 296, in <module>                                                                                     
    sys.exit(main())                                                                                                                       
             ^^^^^^                                                                                                                        
  File "/opt/USD/bin/usdrecord", line 268, in main                                                                                         
    frameRecorder = UsdAppUtils.FrameRecorder(                                                                                             
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                             
pxr.Tf.ErrorException:                                
        Error in 'pxrInternal_v0_24__pxrReserved__::HdRendererPluginRegistry::CreateRenderDelegate' at line 100 in file /src/USD/pxr/imagin
        Error in 'pxrInternal_v0_24__pxrReserved__::UsdImagingGLEngine' at line 205 in file /src/USD/pxr/usdImaging/usdImagingGL/engine.cpp

```

Note that I added the warning in `HgiGLMeetsMinimumRequirements`. Apparently the GL
version string we're getting is `OpenGL ES 3.2 Mesa 23.3.6`. This is obviously not
what we want, we need OpenGL 4.5 or better. 4.5 does seem to be installed and available
on this system, but somehow USD is loading ES instead of regular desktop GL.

Also, notice the SdfPath warning. Why would it be building an SdfPath that looks like
`:1:0(0)`. That almost looks like it's trying to choose a display (the wrong one in
this case) with an SdfPath instead of a string. Starting with an explicit display of
:0 and :1 doesn't change the error.

After some investigation, I notice that other tests do not have the SdfPath error but
still fail with the wrong, ES GL version being loaded. That seems like the issue.

It occurs to me while doing this, Qt is only being used to create a window to back
an OpenGL render. I'm not sure if this is necessary for Vulkan or Metal, I think it
isn't. Also, I know we don't need all the machinery and size of Qt for this, I bet
you could write an SDL backed version of this that would have much less requirements
in a containerized environment. Or if not SDL GLFW or some other cross platform 
context manager, https://github.com/tauri-apps/tao would be nice and small and only
provide minimal windowing, which is what we need. It is Rust though.

Back on track...

On linux platforms the GL library is loaded directly as `libGL.so.1`. In my container
that does seem to point to the correct library. One thing I'm concerned about, is
that I built this container with a lot less setup, and I've been `apk add`ing stuff
as I debug test errors. Maybe there's some configuration issue. I think at this point
I'm going to clean up the dockerfile, rebuild, and take a break.

## Day Three

Doing more investigation today. There are two issues I think (at least)

One, lots of tests fail with diff failures. The first issue here is that the default
`diff` command on alpine doesn't have a `-I` flag. You can fix that with
`apk add diffutils`

After that's fixed, I see the same number of failures, but with actual diffs. 

Two, anywhere Qt is being used to initialize the GL instance, we're getting ES,
like in the error message above. That doesn't seem to be the case if we use the
garch window to initialize opengl, in that case we get 
`4.5 (Compatibility Profile) Mesa 23.3.6` which ought to be minimal but functional.

The garch window class is `GarchGLDebugWindow`. This appears to be a hand setup
minimal window for creating gl contexts on supported platforms. Maybe this is the
way to go for this project, so we're not relying on Qt.

Qt has a number of ways to set it to use a specific GL version, but none of them
seem to be working for me. Options include
- set QT_OPENGL env var to `desktop` or `software`
- early in run call `QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL)`
- early in run call `QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)`

Spent most of today working on this, I think I can make a few conclusions.

1) Qt is not needed in this case. There are ways to control how it configures its
OpenGL context, but those things are not helping and I don't know why. Replacing
it with glfw for initializing a gl context seems to work fine. A more ambitious
goal could be to write a cross platform window/context creator, but passing on
that for now.

2) The diff failures are mostly (entirely?) about constants not being what's
expected. For instance, `GL_UNIFORM_BUFFER_OFFSET_ALIGNMENT` is expected to be
256 explicitly in the tests in several places, and it isn't under this llvmpipe
implementation. Another common class of differences looks like this
```
< uboSize, 480
---
> uboSize, 512
```

As far as I know, it is ok for this GL implementation to specify the constants
it supports. If this is only the tests making incorrect assumptions, then there's
nothing to worry about. If there are such assumptions in the Hydra or Storm
implementation that would be worse. There are around 22 tests failing still that
I havent figured out yet. Getting to the bottom of those would be good. Here's a
list

```
	823 - testHdStBufferAggregation (Failed)
	824 - testHdStBufferArray (Failed)
	825 - testHdStBufferArrayInstancingDisabled (Failed)
	829 - testHdStCodeGen_Mesh_Indirect (Failed)
	830 - testHdStCodeGen_Mesh_Bindless_Indirect (Failed)
	831 - testHdStCodeGen_Mesh_Bindless_Indirect_SmoothNormals (Failed)
	832 - testHdStCodeGen_Mesh_Bindless_Indirect_DoubleSided (Failed)
	833 - testHdStCodeGen_Mesh_Bindless_Indirect_FaceVarying (Failed)
	834 - testHdStCodeGen_Mesh_Indirect_Instance (Failed)
	835 - testHdStCodeGen_Mesh_Bindless_Indirect_Instance (Failed)
	836 - testHdStCodeGen_Mesh_EdgeOnly (Failed)
	837 - testHdStCodeGen_Mesh_EdgeOnly_BlendWireframe (Failed)
	838 - testHdStCodeGen_Curves_Bindless (Failed)
	839 - testHdStCodeGen_Curves_Indirect (Failed)
	840 - testHdStCodeGen_Points_Bindless (Failed)
	841 - testHdStCodeGen_Points_Indirect (Failed)
	850 - testHdStDrawBatching (Failed)
	869 - testHdStHWFaceCulling (Failed)
	870 - testHdStIndirectDrawBatchCodeGen (Failed)
	878 - testHdStInstancing_Div5_Level2 (Failed)
	886 - testHdStPrimvars (Failed)
	904 - testHdxPickResolveMode (Failed)
	1213 - testUsdAppUtilsFrameRecorder (Failed)
```

To get usdrecord working I added this code in place of the Qt context code

```
    try:
        # need to install glfw, pip, and pip install glfw with the breaking flag
        import glfw
        glfw.init()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        window = glfw.create_window(width, height, "offscreen buffer", None, None)
        if not window:
            glfw.terminate()
            return None
        glfw.make_context_current(window)
        return window
        
    except ImportError:

```

Also, for testing I found it useful to vnc into the docker container and run glxgears,
etc. To do that,

```
apk add x11vnc
x11vnc -display :1 -forever &
```

then make sure to run docker with `-p 5900:5900` and connect using `localhost:5900`

Open questions to wrap up the day
- Could this be be basis of a generic USD imaging container, with GL and embree as new containers?
- Can Qt, Pyside, others be removed from the built container?
- Do we really need fluxbox, or is xvfb enough for our use?
- Is even xvfb needed for cases like an embree container? I need it for tests, is that it?
- usdview is disabled, should it be enabled?

I did get a successful render with hacked usdrecord inside the container, and
viewed it with alpine firefox, so, excelsior! I'm declaring victory for today.

I'm starting to get nervous about not committing anything, this is just sitting
in an unversioned local folder. Cleanup and checkpoint would be a good next
goal

# Day Four

After nearly around a month long forced hiatus, I'm back at it. Sure wish I had
gotten things into a stable state and commited.

Working on splitting out the current imaging dockerfile into a few different images,
one of the first hurdles is that alpine 3.20 moved to python 3.12, and USD is not
updated for that version yet, so I'm pinning to alpine 3.19.

Shorter session today, only an hour or so, but I have a couple new images built for
testing. Now to get some renders and verify with the gl version. No embree version
yet, but I can draw kitchen set in the gl image

# Multiday Warnings Investigation

This is an "as I have time" kind of thing

There are quite a few warnings printed on a successful render. Looking into these,

```
  The XKEYBOARD keymap compiler (xkbcomp) reports:
  > Warning:          Could not resolve keysym XF86CameraAccessEnable
  > Warning:          Could not resolve keysym XF86CameraAccessDisable
```

These are common errors reported when two modules are out of date with each other,
the source packages would need changes to fix these. They should be fixed, alpine
has done so in the past:
https://gitlab.alpinelinux.org/alpine/aports/-/issues/12829

```
  xinit: XFree86_VT property unexpectedly has 0 items instead of 1
```

Not sure yet. Online resources for this and other xinit errors have been
surprisingly unhelpful. I'm not sure what this means, but for the moment I'm going
to redirect the stdout and stderr from xinit to a log file. Most online advice is
to just ignore the output, which I don't like because it would mean I'd ignore
valid errors.

```
  Failed to read: session.ignoreBorder
  Setting default value
  Failed to read: session.forcePseudoTransparency
  Setting default value
  Failed to read: session.colorsPerChannel
  Setting default value
  lots of etc.
```

These appear to be coming from fluxbox. Actually, now that I'm not using Qt in the
script fluxbox appears to not be needed, removing it.

```
  MESA: error: ZINK: failed to load libvulkan.so.1
  glx: failed to create drisw screen
  failed to load driver: zink
  Warning: in SdfPath at line 144 of /src/USD/pxr/usd/sdf/path.cpp -- Ill-formed SdfPath <>: :1:0(0): parse error matching pxrInternal_v0_24__pxrReserved__::Sdf_PathParser::Path
```

These errors/warnings are reported by the actual render process. The last one is
an "ill formed SdfPath" error I've seen all the time with this render class, definitely
pxr code. This is probably harmless, but would be nice to get to the bottom of.

The other 3 seem related to attempting to load zink (the vulkan driver) before
falling back to llvmpipe. I suspect that fixing this requires setting up Mesa to default
to llvmpipe.

Note, while evaluating these warnings and fiddling with configuration I confirmed
that I can render without needing Qt at all, which is great, and reduces the image
size by a few hundred megabytes.

# EMBREE

I went back and added embree support to the base image, in order to build the embree
plugin, and made a new derived container that has embree installed for rendering. That
didn't work for the versioning reasons listed below.

Current embree packages in alpine are for embree4. Edge actually supports both 3 and 4,
but I can't use edge because python 3.12 is not ready in USD yet. So, if I roll
back alpine to 3.18 (from 3.19) I can get embree3 for USD. However, in 3.18 there is
no support for pyside in arm platforms. This versionitis is a problem.

I think the path to getting this to work is to build embree 3 in the container
before building USD. If I do that in the main container, dependent containers will
need to have this extra memory. So, I imagine the thing to do will be to have an
embree specific base container. Or maybe not, I'm actually not sure which is the
better tradeoff. Really, we only need embree to exist while we build the plugin,
so the only cost is time to build embree, and memory for the plugin which will
only be used in one derived container.

```
    -DEMBREE_INCLUDE_DIR=/usr/include/embree3 \
    -DEMBREE_LIBRARY=/usr/lib/libembree3.so.3 \
    -DPXR_BUILD_EMBREE_PLUGIN=TRUE \
```

# Wrap Up

Wrapping up this initial investigation. The committed version will have two
images, one base build that has imaging support, and one build derived from
that one, which has a virtual frame buffer and gl support. No high quality
renderer at this time, but the foundation is there. I think getting there is
enough work that it's worth checkpointing here first.

Note that no changes appear to be needed to the USD branch, which is nice. I
did rewrite the usdrender script for the container, to avoid needing Qt.

I built and pushed those versions with these command lines:

```
docker buildx build --platform linux/arm64,linux/amd64 --tag rstelzleni/usd-alpine:imaging-24.05 --tag rstelzleni/usd-alpine:imaging-latest --builder=multi-builder -f Dockerfile.imaging-base --push .
docker buildx build --platform linux/arm64,linux/amd64 --tag rstelzleni/usd-alpine:gl-24.05 --tag rstelzleni/usd-alpine:gl-latest --builder=multi-builder -f Dockerfile.gl --push .
```
