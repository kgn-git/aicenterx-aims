import {Config} from "@remotion/cli/config";

// Every fragment is encoded with the same settings, so #32 can join the approved fragments with ffmpeg's concat
// demuxer without re-encoding them.
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setColorSpace("bt709");
Config.setCrf(18);
Config.setAudioCodec("aac");
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
