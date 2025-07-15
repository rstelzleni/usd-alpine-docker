from pxr import Usd
from pxr import UsdRender
from pxr import Sdf
from pxr import UsdAppUtils
from pxr import Tf

import argparse
import logging
import os
import sys


logger = logging.getLogger(__name__)


def _SetupOpenGLContext(width=100, height=100):
    import glfw

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(width, height, "offscreen buffer", None, None)
    if not window:
        glfw.terminate()
        return None
    glfw.make_context_current(window)
    return window


def main():
    programName = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(
        prog=programName, description="Generates images from a USD file"
    )

    # Positional (required) arguments.
    parser.add_argument(
        "usdFilePath", action="store", type=str, help="USD file to record"
    )
    parser.add_argument(
        "outputImagePath",
        action="store",
        type=str,
        help=(
            "Output image path. For frame ranges, the path must contain "
            'exactly one frame number placeholder of the form "###" or '
            '"###.###". Note that the number of hash marks is variable in '
            "each group."
        ),
    )

    # Optional arguments.
    parser.add_argument(
        "--mask",
        action="store",
        type=str,
        dest="populationMask",
        metavar="PRIMPATH[,PRIMPATH...]",
        help=(
            "Limit stage population to these prims, their descendants and "
            "ancestors. To specify multiple paths, either use commas with no "
            "spaces or quote the argument and separate paths by commas and/or "
            "spaces."
        ),
    )

    parser.add_argument(
        "--purposes",
        action="store",
        type=str,
        dest="purposes",
        metavar="PURPOSE[,PURPOSE...]",
        default="proxy",
        help=(
            "Specify which UsdGeomImageable purposes should be included "
            'in the renders.  The "default" purpose is automatically included, '
            "so you need specify only the *additional* purposes.  If you want "
            "more than one extra purpose, either use commas with no spaces or "
            "quote the argument and separate purposes by commas and/or spaces."
        ),
    )

    parser.add_argument(
        "--sessionLayer",
        action="store",
        type=str,
        dest="sessionLayerPath",
        metavar="SESSIONLAYER",
        help=(
            "If specified, the stage will be opened with the "
            "'sessionLayer' in place of the default anonymous layer."
        ),
    )

    # Note: The argument passed via the command line (disableGpu) is inverted
    # from the variable in which it is stored (gpuEnabled).
    parser.add_argument(
        "--disableGpu",
        action="store_false",
        dest="gpuEnabled",
        help=(
            "Indicates if the GPU should not be used for rendering. If set "
            "this not only restricts renderers to those which only run on "
            "the CPU, but additionally it will prevent any tasks that require "
            "the GPU from being invoked."
        ),
    )

    # Note: The argument passed via the command line (disableCameraLight)
    # is inverted from the variable in which it is stored (cameraLightEnabled)
    parser.add_argument(
        "--disableCameraLight",
        action="store_false",
        dest="cameraLightEnabled",
        help=(
            "Indicates if the default camera lights should not be used "
            "for rendering."
        ),
    )

    UsdAppUtils.cameraArgs.AddCmdlineArgs(parser)
    UsdAppUtils.framesArgs.AddCmdlineArgs(parser)
    UsdAppUtils.complexityArgs.AddCmdlineArgs(parser)
    UsdAppUtils.colorArgs.AddCmdlineArgs(parser)
    UsdAppUtils.rendererArgs.AddCmdlineArgs(parser)

    parser.add_argument(
        "--imageWidth",
        "-w",
        action="store",
        type=int,
        default=960,
        help=(
            "Width of the output image. The height will be computed from this "
            "value and the camera's aspect ratio (default=%(default)s)"
        ),
    )

    parser.add_argument(
        "--renderPassPrimPath",
        "-rp",
        action="store",
        type=str,
        dest="rpPrimPath",
        help=(
            "Specify the Render Pass Prim to use to render the given "
            "usdFile. "
            "Note that if a renderSettingsPrimPath has been specified in the "
            "stage metadata, using this argument will override that opinion. "
            "Furthermore any properties authored on the RenderSettings will "
            "override other arguments (imageWidth, camera, outputImagePath)"
        ),
    )

    parser.add_argument(
        "--renderSettingsPrimPath",
        "-rs",
        action="store",
        type=str,
        dest="rsPrimPath",
        help=(
            "Specify the Render Settings Prim to use to render the given "
            "usdFile. "
            "Note that if a renderSettingsPrimPath has been specified in the "
            "stage metadata, using this argument will override that opinion. "
            "Furthermore any properties authored on the RenderSettings will "
            "override other arguments (imageWidth, camera, outputImagePath)"
        ),
    )

    args = parser.parse_args()

    args.imageWidth = max(args.imageWidth, 1)

    purposes = args.purposes.replace(",", " ").split()

    # Load the root layer.
    rootLayer = Sdf.Layer.FindOrOpen(args.usdFilePath)
    if not rootLayer:
        logger.error("Could not open layer: %s" % args.usdFilePath)
        return 1

    # Load the session layer.
    if args.sessionLayerPath:
        sessionLayer = Sdf.Layer.FindOrOpen(args.sessionLayerPath)
        if not sessionLayer:
            logger.error("Could not open layer: %s" % args.sessionLayerPath)
            return 1
    else:
        sessionLayer = Sdf.Layer.CreateAnonymous()

    # Open the USD stage, using a population mask if paths were given.
    if args.populationMask:
        populationMaskPaths = args.populationMask.replace(",", " ").split()

        populationMask = Usd.StagePopulationMask()
        for maskPath in populationMaskPaths:
            populationMask.Add(maskPath)

        usdStage = Usd.Stage.OpenMasked(rootLayer, sessionLayer, populationMask)
    else:
        usdStage = Usd.Stage.Open(rootLayer, sessionLayer)

    if not usdStage:
        logger.error("Could not open USD stage: %s" % args.usdFilePath)
        return 1

    UsdAppUtils.framesArgs.ValidateCmdlineArgs(
        parser, args, usdStage, frameFormatArgName="outputImagePath"
    )

    # Get the camera at the given path (or with the given name).
    usdCamera = UsdAppUtils.GetCameraAtPath(usdStage, args.camera)

    # Get the RenderSettings Prim Path.
    # It may be specified directly (--renderSettingsPrimPath),
    # via a render pass (--renderPassPrimPath),
    # or by stage metadata (renderSettingsPrimPath).
    if args.rsPrimPath and args.rpPrimPath:
        logger.error(
            "Cannot specify both --renderSettingsPrimPath and --renderPassPrimPath"
        )
        return 1
    if args.rpPrimPath:
        # A pass was specified, so next we get the associated settings prim.
        renderPass = UsdRender.Pass(usdStage.GetPrimAtPath(args.rpPrimPath))
        if not renderPass:
            logger.error("Unknown render pass <{}>".format(args.rpPrimPath))
            return 1
        sourceRelTargets = renderPass.GetRenderSourceRel().GetTargets()
        if not sourceRelTargets:
            logger.error("Render source not authored on {}".format(args.rpPrimPath))
            return 1
        args.rsPrimPath = sourceRelTargets[0]
        if len(sourceRelTargets) > 1:
            Tf.Warn(
                "Render pass <{}> has multiple targets; using <{}>".format(
                    args.rpPrimPath, args.rsPrimPath
                )
            )
    if not args.rsPrimPath:
        # Fall back to stage metadata.
        args.rsPrimPath = usdStage.GetMetadata("renderSettingsPrimPath")

    if args.gpuEnabled:
        # UsdAppUtils.FrameRecorder will expect that an OpenGL context has
        # been created and made current if the GPU is enabled.
        #
        # Note that the size of the widget doesn't actually affect the size of
        # the output image. We just pass it along for cleanliness.
        glWidget = _SetupOpenGLContext(args.imageWidth, args.imageWidth)

    rendererPluginId = (
        UsdAppUtils.rendererArgs.GetPluginIdFromArgument(args.rendererPlugin) or ""
    )

    # Initialize FrameRecorder
    frameRecorder = UsdAppUtils.FrameRecorder(
        rendererPluginId, args.gpuEnabled
    )
    frameRecorder.SetImageWidth(args.imageWidth)
    frameRecorder.SetComplexity(args.complexity.value)
    frameRecorder.SetCameraLightEnabled(args.cameraLightEnabled)
    frameRecorder.SetColorCorrectionMode(args.colorCorrectionMode)
    frameRecorder.SetIncludedPurposes(purposes)

    logger.info("Camera: %s" % usdCamera.GetPath().pathString)
    logger.info("Renderer plugin: %s" % frameRecorder.GetCurrentRendererId())

    for timeCode in args.frames:
        logger.info("Recording time code: %s" % timeCode)
        outputImagePath = args.outputImagePath.format(frame=timeCode)
        try:
            frameRecorder.Record(usdStage, usdCamera, timeCode, outputImagePath)
        except Tf.ErrorException as e:

            logger.error(
                "Recording aborted due to the following failure at time code "
                "{0}: {1}".format(timeCode, str(e))
            )
            break

    # The framerecorder needs to be deliberately released before exit
    frameRecorder = None


if __name__ == "__main__":
    sys.exit(main())
