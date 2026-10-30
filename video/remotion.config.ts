import {Config} from "@remotion/cli/config";

// The fragments and the one-piece video share these settings, so a fragment under review looks like the released
// video.
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setColorSpace("bt709");
Config.setCrf(18);
Config.setAudioCodec("aac");
Config.setEnforceAudioTrack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
