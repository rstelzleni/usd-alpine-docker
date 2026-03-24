# Build for 26.03

Patching the changes for alpine/musl went pretty smoothly, there were only
a few small changes to get things working, mostly places where the WASM
work needed to change the same lines I did.

Alpine version now pinned to 3.23.3 to avoid binary breakages on minor package
updates. This isn't an issue unless you want to build plugins against these
images, but if you do it's a frustrating experience.

Python version 3.12

## Tests

The tests that still fail are below.

In the core image:

```
The following tests FAILED:
    72 - testArchStackTrace (Failed)
Errors while running CTest
```

I believe we're down to only one owing to the WASM work. This stack trace test
has never worked in the alpine images, but we still seem to get valid stack
traces. I may look into this, but feel it is not urgent.

The imaging tests still required the same testing file hacks as in the 25.05
notes. Once I fixed those testing utilities to work in our headless software gl
environment, we are down to only 13 imaging test failures.

```
        1060 - testHdStCodeGen_GL_Mesh_Indirect (Failed)
        1061 - testHdStCodeGen_GL_Mesh_Indirect_SmoothNormals (Failed)
        1062 - testHdStCodeGen_GL_Mesh_Indirect_DoubleSided (Failed)
        1063 - testHdStCodeGen_GL_Mesh_Indirect_FaceVarying (Failed)
        1064 - testHdStCodeGen_GL_Mesh_Indirect_Instance (Failed)
        1065 - testHdStCodeGen_GL_Mesh_EdgeOnly (Failed)
        1066 - testHdStCodeGen_GL_Mesh_EdgeOnly_BlendWireframe (Failed)
        1067 - testHdStCodeGen_GL_Curves_Indirect (Failed)
        1068 - testHdStCodeGen_GL_Points_Indirect (Failed)
        1105 - testHdStInstancing_Div5_Level2 (Failed)
        1131 - testHdxPickResolveMode (Failed)
        1231 - testUsdImagingGLPickAndHighlight (Failed)
        1232 - testUsdImagingGLPickAndHighlight_SceneIndex (Failed)
```

The HdStCodeGen failures seem to be related to extensions like
GL_NV_shader_buffer_load, GL_NV_gpu_shader5 and GL_ARB_bindless_texture, which
we do not have in our software GL environment

testHdStInstancing_Div5_Level2 seems to be related to the number of vertex shader
storage blocks available in llvmpipe. We don't have as many as it wants.

The UsdImagingGLPickAndHighlight failures seem to be related to the function
UsdImagingGLEngine::TestIntersection, which is surprising. See the notes from
the 25.05 for more details. Since we don't support interactive picking I
haven't gotten to the bottom of these. Same for testHdxPickResolveMode.

