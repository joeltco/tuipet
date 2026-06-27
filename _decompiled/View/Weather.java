/*
 * Decompiled with CFR 0.152.
 */
package View;

import Model.Enum;
import View.DisplayPane;
import View.Polygon;
import View.SoundConfig;
import View.SoundObj;
import View.SpriteObj;
import View.ViewUtil;
import java.awt.Component;
import java.util.Random;
import javax.sound.sampled.Clip;
import javax.swing.Icon;

public class Weather {
    private final String MOD_FOLDER;
    private final String RESOURCES_FOLDER;
    private Random _random = new Random();
    private SoundObj _sounds;
    private byte _scale;
    private DisplayPane _overlay = new DisplayPane(false);
    private final int WIDTH;
    private final int HEIGHT;
    private Clip _longClip;
    private boolean _thunder;
    private int _lightningCount;
    private int _alpha;
    private int _blue;
    private int _red;

    public boolean getThunder() {
        return this._thunder;
    }

    public DisplayPane getOverlay() {
        return this._overlay;
    }

    public void setOverlaySize(int width, int height) {
        this._overlay.setSize(width, height);
    }

    public void setOverlayLocation(int x, int y) {
        this._overlay.setLocation(x, y);
    }

    public Weather(byte scale, int animWinLocXMax, int animWinLocYMax, SoundObj sounds, String modFolder, String resourcesFolder) {
        this.MOD_FOLDER = modFolder;
        this.RESOURCES_FOLDER = resourcesFolder;
        this._sounds = sounds;
        this._scale = scale;
        this.WIDTH = 6;
        this.HEIGHT = 8;
        SpriteObj spriteSheet = new SpriteObj(this.MOD_FOLDER, this.RESOURCES_FOLDER, "weather.png", this._overlay, this.WIDTH, this.HEIGHT, scale);
        spriteSheet.setSpriteSheet(ViewUtil.divideSpriteSheet(spriteSheet.getSpriteLoc(), 3, this.WIDTH, this.HEIGHT, scale));
        Icon[] precip = spriteSheet.getSpriteSheet();
        this._overlay.removeAll();
        this._overlay.repaint();
        for (int i = 0; i < 200; ++i) {
            SpriteObj drop = new SpriteObj();
            drop.setSpriteSheet(precip);
            drop.setVisible(true);
            drop.setScale(this._scale);
            drop.setSize(this.WIDTH, this.HEIGHT);
            this._overlay.add(drop);
        }
    }

    public void startWeather(Enum.Weather weather) {
        this.stopWeather();
        if (this._longClip == null) {
            switch (weather) {
                case Raining: {
                    this.changeIntensity(125);
                    break;
                }
                case Drizzling: {
                    this.changeIntensity(50);
                    break;
                }
                case HeavyRain: {
                    this.changeIntensity(200);
                    break;
                }
                case LightSnow: {
                    this.changeIntensity(50);
                    break;
                }
                case HeavySnow: {
                    this.changeIntensity(200);
                    break;
                }
                case Snowing: {
                    this.changeIntensity(125);
                }
            }
            this.startSound(weather);
        }
    }

    private void startSound(Enum.Weather weather) {
        switch (weather) {
            case Raining: {
                this._longClip = this._sounds.loopSound(SoundConfig._rainLoop, SoundConfig._effectsVolume * 0.66f);
                break;
            }
            case Drizzling: {
                this._longClip = this._sounds.loopSound(SoundConfig._drizzleLoop, SoundConfig._effectsVolume * 0.33f);
                break;
            }
            case HeavyRain: {
                this._longClip = this._sounds.loopSound(SoundConfig._heavyRainLoop, SoundConfig._effectsVolume);
                break;
            }
            case LightSnow: {
                this._longClip = this._sounds.loopSound(SoundConfig._lightSnowLoop, SoundConfig._effectsVolume * 0.33f);
                break;
            }
            case HeavySnow: {
                this._longClip = this._sounds.loopSound(SoundConfig._heavySnowLoop, SoundConfig._effectsVolume);
                break;
            }
            case Snowing: {
                this._longClip = this._sounds.loopSound(SoundConfig._snowLoop, SoundConfig._effectsVolume * 0.66f);
            }
        }
    }

    public void toggleWeatherSound(boolean run, Enum.Weather weather) {
        if (this._longClip != null) {
            if (run && !this._longClip.isActive()) {
                this._longClip.start();
            } else if (!run && this._longClip.isActive()) {
                this._longClip.stop();
            }
        }
    }

    private void changeIntensity(int drops) {
        this.invisibleDrops();
        for (int i = 0; i < drops - 1; ++i) {
            this._overlay.getComponent(i).setVisible(true);
        }
    }

    private void invisibleDrops() {
        for (Component c : this._overlay.getComponents()) {
            c.setVisible(false);
        }
    }

    public void stopWeather() {
        if (this._longClip != null) {
            this._longClip.stop();
            this._longClip.flush();
            this._longClip.close();
            this._longClip = null;
        }
        this._thunder = false;
    }

    public void precipitate(Enum.Weather weather, int delay, Polygon rect) {
        for (Component d : this._overlay.getComponents()) {
            this.moveDown((SpriteObj)d, weather, delay);
        }
        if (weather == Enum.Weather.HeavyRain) {
            int prob = this._random.nextInt(500);
            if (prob == 0) {
                if (!this._thunder) {
                    this._alpha = rect.getAlpha();
                    this._red = rect.getRed();
                    this._blue = rect.getBlue();
                }
                this._thunder = true;
            }
            this.checkThunder(rect);
        } else {
            this._thunder = false;
        }
    }

    private void checkThunder(Polygon rect) {
        int rate = 2;
        if (this._thunder) {
            if (this._lightningCount >= rate * 5 && this._lightningCount % rate == 0) {
                rect.changeColor(0, 0, 0, 0);
            } else {
                rect.changeColor(this._red, 0, this._blue, this._alpha);
            }
            if (this._lightningCount > rate * 5) {
                if (this._lightningCount == rate * 5 + 1) {
                    int soundProb = this._random.nextInt(5);
                    if (soundProb == 0) {
                        this._sounds.playSound(SoundConfig._sharpThunder, SoundConfig._effectsVolume * 0.33f);
                    } else if (soundProb <= 2) {
                        this._sounds.playSound(SoundConfig._longThunder, SoundConfig._effectsVolume);
                    } else {
                        this._sounds.playSound(SoundConfig._shortThunder, SoundConfig._effectsVolume);
                    }
                } else if (this._lightningCount > rate * 5 + rate * (this._random.nextInt(3) + 1)) {
                    this._lightningCount = 0;
                    rect.changeColor(this._red, 0, this._blue, this._alpha);
                    this._thunder = false;
                    return;
                }
            }
            ++this._lightningCount;
        }
    }

    private void moveDown(SpriteObj precip, Enum.Weather weather, int delay) {
        if ((double)precip.getY() + (double)this.HEIGHT * 1.2 * (double)this._scale >= (double)this._overlay.getHeight()) {
            int x = this._random.nextInt(this._overlay.getWidth() / this._scale + 120) - 80;
            int y = this._random.nextInt(this._overlay.getHeight() / this._scale) * -1;
            this.randomizeIcon(precip, weather);
            precip.setLoc(x, y - precip.getHeight() / this._scale);
        }
        if (weather == Enum.Weather.Raining || weather == Enum.Weather.Drizzling || weather == Enum.Weather.HeavyRain) {
            int rate = 10;
            precip.setLoc(precip.getX() / this._scale + rate, precip.getY() / this._scale + rate * 2);
        } else if ((weather == Enum.Weather.Snowing || weather == Enum.Weather.LightSnow || weather == Enum.Weather.HeavySnow) && delay == 0) {
            int rate = 5;
            int movement = this._random.nextInt(rate * 2) - 1;
            precip.setLoc(precip.getX() / this._scale + movement, precip.getY() / this._scale + rate);
        }
    }

    private void randomizeIcon(SpriteObj drop, Enum.Weather weather) {
        int inc = 0;
        if (weather == Enum.Weather.Snowing || weather == Enum.Weather.HeavySnow || weather == Enum.Weather.LightSnow) {
            inc = 3;
        }
        int r = this._random.nextInt(3) + inc;
        drop.setIcon(drop.getSpriteSheet()[r]);
    }
}

