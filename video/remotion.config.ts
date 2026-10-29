import {Config} from "@remotion/cli/config";

// Every fragment is encoded with the same settings and always carries an audio track, even while silent, so the
// approved fragments can be joined with ffmpeg's concat demuxer without re-encoding them.
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setColorSpace("bt709");
Config.setCrf(18);
Config.setAudioCodec("aac");
Config.setEnforceAudioTrack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
