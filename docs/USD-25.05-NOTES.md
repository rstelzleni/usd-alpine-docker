# Build for 25.05

This actually went pretty smoothly. Major notes are:

- OneTBB

USD supports a modern enough TBB that I could move off of my patched legacy
build. This is great, since it means we can use the alpine package.

It also means we no longer need the /opt/vendored folder. We can now depend
entirely on alpine packages for our dependencies.

- Python 3.12

This is the _newest_ version of Python that USD supports, and luckily alpine
has not moved to 3.13 yet. So, it's the version in this image.

- USD patches

I still needed to patch Arch in USD to get it to build under musl. My patches
are

https://github.com/rstelzleni/USD/commit/a11f3b636a7b99a1275e8ecdcec0b1ec4cb067b1
https://github.com/rstelzleni/USD/commit/f1fcdc0b3bbd1ef4a98cd28abf4e301764863bea
https://github.com/rstelzleni/USD/commit/4cf168d279fcb91b2a82694d3b9a38cb4c2769e6
https://github.com/rstelzleni/USD/commit/ee98a457110666657478999568195a2d9de7a28e
https://github.com/rstelzleni/USD/commit/ee98a457110666657478999568195a2d9de7a28e
https://github.com/rstelzleni/USD/commit/4e0e861375f3f11304ed7cd80d5946eff30c5ad7

Some of those overwrite previous patches, where I found better fixes.

I found this OpenUSD issue, it may be worth offering a PR.

https://github.com/PixarAnimationStudios/OpenUSD/issues/2939

## Tests

Before running tests I needed to

```
apk add diffutils
```

The base alpine image uses busybox diff, which does not support the
--strip-trailing-cr option that the tests expect. This makes hundreds of tests
fail, especially in Pcp. Installing diffutils gets the gnu diff that has the
flag. I only added this in the builder, not the release image.

Once that was done, 3 tests failed:

```
         77 - testArchStackTrace (Failed)
        237 - testTsSplineSampling (Failed)
        635 - testUsdSkelBakeSkinning (Failed)
```

testArchStackTrace has never passed in these alpine images. I'm not sure why,
but in general it seems like we're not getting the stack traces we'd expect.
for now I'm letting this be broken

I'm not worried about the testTsSplineSampling failure, since this feature is
not released. For what its worth, the failures are about tangent line lengths.

The testUsdSkelBakeSkinning failure is an issue with precision of floating
point output in strings. I'm not worried about this ether, the test should do a
diff with epsilon instead of string diffs. Example failure output

```
<         12: [(-0.60701656, -1.1, -0.55), (1.1500001, 1.2307667, 0.9687131)],
---
>         12: [(-0.6070165, -1.1, -0.55), (1.1500001, 1.2307667, 0.9687131)],
```

## Imaging

The imaging container can now be built with the newest alpine release, which is
great. I don't recall why I had to pin to an older one before, but I'm glad to
have that resolved upstream.

libOpenCL is now required for imaging, so I added opencl the alpine package.

### Test env setup

I edited the comments in the dockerfile to show some of the environment I
needed for running tests. Additionally it can be helpful to set MESA_DEBUG=1

### Note on GLXFBConfig

When creating the Garch_GLPlatformDebugWindow, it fails to get a compatible
GLXFBConfig. This causes all imaging tests to fail. The code hasn't changed
in a long time, so I suspect this is a difference in the alpine/llvmpipe/mesa
setup since the last version of alpine I used.

The GLXFBConfigs that are available all have GLX_SAMPLES_ARB set to 0. In the
requested attributes USD is setting GLX_SAMPLE_BUFFERS to 0, which seems
correct in this environment, but it is setting GLX_SAMPLES to 1. Since we only
have 0, we don't get a compatible config.

I hacked this to work by hard coding the GLX_SAMPLES to 0 in 
Garch_GLPlatformDebugWindow::Init. After doing so graphical tests can run in the
container.

This class is not used when offline rendering, so this seems to be a problem for
the tests, but not for our actual rendering implementation.

### GlfTestGLContext

Same issue exists as above, only in this case it hard codes the sample buffers
to 1 and samples to 4. Need to be 0 and o, unless multisample can be enabled in
mesa/llvmpipe.

### Note on not using Qt

I didn't install Qt for tests, but did edit usdrecord to include this snippet
for getting a window. testUsdAppUtilsFrameRecorder.py needs the same change.

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

### Tests still failing

There are 14 tests still failing (17 counting the non-imaging tests). Notes on
these are below.

- testUsdImagingGLPickAndHighlight
- testUsdImagingGLPickAndHighlight_SceneIndex
- testHdxPickResolveMode

At first I thought these might fail because we aren't running a desktop with a
mouse, but on closer inspection I don't think that's being exercised. The
function UsdImagingGLEngine::TestIntersection seems to be failing and I'm not
sure why. In our use case this isn't a problem since we're not doing any picking,
but it would be good to understand this at some point.

In the Hdx case, it's interesting that some Hdx picking tests do pass.

- testHdStInstancing_Div5_Level2

This appears to fail because llvmpipe 20.1.7 doesn't offer enough vertex shader
storage blocks. The glsl shaders compiling want 17 or 18 blocks, but only 16
are available.

- testHdStCodeGen*

There are 9 of these.

They seem to fail because they expect the presence of some extensions we don't
have. This includes at least GL_NV_shader_buffer_load, GL_NV_gpu_shader5 and
GL_ARB_bindless_texture. Since some of these are NVIDIA specific, I suspect these
tests are only expected to pass on specific test hardware. I'm not digging too
much deeper, I just made a cursory check to see if they're failing because of
test machine specs.

- testHdStIndirectDrawBatchCodeGen

This one gives a number of errors related to reporting issues when compiling
an invalid shader. I suspect the failure could be related to different reporting
of errors in the glsl compiler.

