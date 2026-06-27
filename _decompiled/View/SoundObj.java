/*
 * Decompiled with CFR 0.152.
 */
package View;

import Model.ViewSettings;
import View.SoundConfig;
import View.ViewUtil;
import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import javax.sound.sampled.FloatControl;
import javax.sound.sampled.Line;
import javax.sound.sampled.LineEvent;
import javax.sound.sampled.LineListener;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.UnsupportedAudioFileException;

public class SoundObj {
    private final String MOD_FOLDER;
    private final String RESOURCES_FOLDER;
    private final ViewSettings _view;
    private final Map<String, Clip> _clips = new HashMap<String, Clip>();

    public SoundObj(String modFolder, String resourcesFolder, ViewSettings view) {
        this.MOD_FOLDER = modFolder + "sounds" + File.separator;
        this.RESOURCES_FOLDER = resourcesFolder + "sounds/";
        this._view = view;
        this.initClips();
    }

    private void initClips() {
        this.insertClip(SoundConfig._select);
    }

    private void insertClip(String name) {
        try {
            Clip clip = (Clip)AudioSystem.getLine(new Line.Info(Clip.class));
            clip.open(AudioSystem.getAudioInputStream(this.getURL(name)));
            this.setVolume(clip, SoundConfig._masterVolume);
            this._clips.put(name, clip);
        }
        catch (Exception ex) {
            System.out.println(ex.getMessage());
        }
    }

    private URL getURL(String name) {
        URL url = null;
        try {
            url = ViewUtil.getURLResource(this.getClass(), this.MOD_FOLDER, this.RESOURCES_FOLDER, name + ".wav");
        }
        catch (Exception e) {
            System.out.println(e.getMessage());
        }
        return url;
    }

    public double getClipLength(String name) {
        double durationInSeconds = -1.0;
        try {
            AudioInputStream is = AudioSystem.getAudioInputStream(this.getURL(name));
            AudioFormat format = is.getFormat();
            long frames = is.getFrameLength();
            durationInSeconds = ((double)frames + 0.0) / (double)format.getFrameRate();
        }
        catch (IOException | IllegalArgumentException | UnsupportedAudioFileException ex) {
            Logger.getLogger(SoundObj.class.getName()).log(Level.SEVERE, null, ex);
        }
        return durationInSeconds;
    }

    private Clip openClip(URL url) {
        Clip clip;
        try {
            AudioInputStream stream = AudioSystem.getAudioInputStream(url);
            clip = AudioSystem.getClip();
            clip.open(stream);
        }
        catch (IOException | IllegalArgumentException | LineUnavailableException | UnsupportedAudioFileException ex) {
            Logger.getLogger(SoundObj.class.getName()).log(Level.SEVERE, null, ex);
            clip = null;
        }
        return clip;
    }

    private Clip openClip(URL url, boolean f) {
        Clip clip;
        try {
            AudioInputStream stream = AudioSystem.getAudioInputStream(url);
            AudioFormat format = stream.getFormat();
            byte[] b = stream.readAllBytes();
            ArrayList<Byte> newSamples = new ArrayList<Byte>();
            for (int i = 0; i < b.length; ++i) {
                if (i % 2 != 0) continue;
                newSamples.add(b[i]);
            }
            byte[] samples = new byte[newSamples.size()];
            for (int i = 0; i < newSamples.size(); ++i) {
                samples[i] = (Byte)newSamples.get(i);
            }
            clip = AudioSystem.getClip();
            clip.open(format, samples, 0, 2);
        }
        catch (IOException | IllegalArgumentException | LineUnavailableException | UnsupportedAudioFileException ex) {
            Logger.getLogger(SoundObj.class.getName()).log(Level.SEVERE, null, ex);
            clip = null;
        }
        return clip;
    }

    private Clip getClip(String fileName) {
        if (this._clips.containsKey(fileName)) {
            return this._clips.get(fileName);
        }
        return this.openClip(this.getURL(fileName));
    }

    public Clip playSound(String fileName) {
        return this.playSound(fileName, SoundConfig._masterVolume);
    }

    public Clip playSound(String fileName, float level) {
        if (this._view.isSound() && !fileName.isEmpty()) {
            Clip finalClip = this.getClip(fileName);
            if (finalClip != null) {
                this.setVolume(finalClip, level);
                if (this._clips.containsKey(fileName)) {
                    this.playClip(finalClip);
                } else {
                    this.playURL(finalClip);
                }
            }
            return finalClip;
        }
        return null;
    }

    private Clip playClip(Clip clip) {
        clip.setFramePosition(0);
        clip.start();
        return clip;
    }

    private Clip playURL(final Clip clip) {
        try {
            clip.addLineListener(new LineListener(){
                final /* synthetic */ SoundObj this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void update(LineEvent event) {
                    if (event.getType() == LineEvent.Type.STOP) {
                        this.this$0.closeSound(clip, this);
                    }
                }
            });
            clip.start();
            return clip;
        }
        catch (Exception exc) {
            exc.printStackTrace(System.out);
            return null;
        }
    }

    private Clip loopClip(Clip clip, int times) {
        clip.setFramePosition(0);
        clip.loop(times);
        return clip;
    }

    private Clip loopURL(final Clip clip, final int times) {
        try {
            clip.addLineListener(new LineListener(){
                final /* synthetic */ SoundObj this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void update(LineEvent event) {
                    if (event.getType() == LineEvent.Type.START) {
                        clip.loop(times);
                    } else if (event.getType() != LineEvent.Type.STOP && event.getType() == LineEvent.Type.CLOSE) {
                        clip.removeLineListener(this);
                    }
                }
            });
            clip.loop(times);
            return clip;
        }
        catch (Exception exc) {
            exc.printStackTrace(System.out);
            return null;
        }
    }

    public Clip loopSound(String fileName, float level) {
        return this.loopSound(fileName, -1, level);
    }

    public Clip loopSound(String fileName, int times) {
        return this.loopSound(fileName, times, SoundConfig._masterVolume);
    }

    public Clip loopSound(String fileName, int times, float level) {
        if (this._view.isSound() && !fileName.isEmpty()) {
            Clip finalClip = this.getClip(fileName);
            if (finalClip != null) {
                this.setVolume(finalClip, level);
                try {
                    if (this._clips.containsKey(fileName)) {
                        this.loopClip(finalClip, times);
                    } else {
                        this.loopURL(finalClip, times);
                    }
                }
                catch (Exception exc) {
                    exc.printStackTrace(System.out);
                }
            }
            return finalClip;
        }
        return null;
    }

    private void closeSound(final Clip clip, final LineListener l) {
        new Thread(null, new Runnable(){
            final /* synthetic */ SoundObj this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                clip.removeLineListener(l);
                clip.close();
            }
        }, "CloseSound").start();
    }

    private void setVolume(Clip clip, float level) {
        if (level != 1.0f) {
            if (level > SoundConfig._masterVolume) {
                level = SoundConfig._masterVolume;
            }
            if (level < 0.0f) {
                level = 0.0f;
            }
            FloatControl volume = (FloatControl)clip.getControl(FloatControl.Type.MASTER_GAIN);
            volume.setValue(20.0f * (float)Math.log10(level));
        }
    }
}

