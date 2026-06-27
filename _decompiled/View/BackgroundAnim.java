/*
 * Decompiled with CFR 0.152.
 */
package View;

import Controller.Utility;
import Model.Battle;
import Model.Enum;
import Model.Habitat;
import Model.PhysicalState;
import View.Polygon;
import View.SpriteObj;
import View.ViewConfig;
import View.ViewUtil;
import java.awt.AlphaComposite;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import javax.swing.Icon;
import javax.swing.ImageIcon;

public class BackgroundAnim {
    private final String MOD_FOLDER;
    private final String RESOURCES_FOLDER;
    private SpriteObj _background;
    private Polygon _rect;
    private int _targetRed;
    private int _targetBlue;
    private int _targetAlpha;
    private BufferedImage _targetImage;
    private BufferedImage _oldIcon;
    private float _currentOpacity = 1.0f;
    private double _rate = 10.0;
    private double _displayedHabitat = -1.0;

    public BackgroundAnim(SpriteObj b, Polygon r, String modFolder, String resourcesFolder) {
        this(b, r, 0, 0, 0, null, modFolder, resourcesFolder);
    }

    public BackgroundAnim(SpriteObj b, Polygon r, int red, int blue, int alpha, BufferedImage bi, String modFolder, String resourcesFolder) {
        this.MOD_FOLDER = modFolder;
        this.RESOURCES_FOLDER = resourcesFolder;
        this._background = b;
        this._rect = r;
        this._targetRed = red;
        this._targetBlue = blue;
        this._targetAlpha = alpha;
        this._targetImage = bi;
        this.setOldIconFromBackground();
    }

    private synchronized void setOldIconFromBackground() {
        Icon icon = this._background.getIcon();
        if (icon != null) {
            this._oldIcon = ViewUtil.createBuffImage(icon);
        }
    }

    private synchronized void setAnimValues(int red, int blue, int alpha, BufferedImage i) {
        this._targetRed = red;
        this._targetBlue = blue;
        this._targetAlpha = alpha;
        if (i != null) {
            this._targetImage = i;
        }
    }

    public synchronized boolean animate(Enum.Menu m) {
        boolean back = this.animateBack();
        boolean tint = this.animateTint();
        return back || tint;
    }

    public synchronized boolean animateTint() {
        boolean tintAnimating;
        if (this._rect.getRed() != this._targetRed || this._rect.getBlue() != this._targetBlue || this._rect.getAlpha() != this._targetAlpha) {
            tintAnimating = true;
            int red = this.adjust(this._rect.getRed(), this._targetRed, this._rate);
            int blue = this.adjust(this._rect.getBlue(), this._targetBlue, this._rate);
            int alpha = this.adjust(this._rect.getAlpha(), this._targetAlpha, this._rate);
            this._rect.changeColor(red, 0, blue, alpha);
        } else {
            tintAnimating = false;
            this._rate = 10.0;
        }
        return tintAnimating;
    }

    private synchronized int adjust(int current, int target, double rate) {
        rate = target != 0 ? (double)target / rate : (double)current / rate;
        if (current != target && current >= 0) {
            int adjusted;
            if (current > target) {
                adjusted = (int)((double)current + (rate *= -1.0));
                if (adjusted < target) {
                    adjusted = target;
                }
            } else {
                adjusted = (int)((double)current + rate);
                if (adjusted > target) {
                    adjusted = target;
                }
            }
            return adjusted;
        }
        return target;
    }

    private synchronized boolean animateBack() {
        boolean backAnimating = false;
        if (this._targetImage != null) {
            if (this._oldIcon == null) {
                this.setOldIconFromBackground();
            }
            backAnimating = true;
            this._currentOpacity += ViewConfig._backgroundOpacityChange;
            if (this._currentOpacity <= 0.0f) {
                this._currentOpacity = 0.0f;
                backAnimating = false;
                this._oldIcon = this._targetImage;
                this._targetImage = null;
                this._currentOpacity = 1.0f;
                this._background.setIcon(new ImageIcon(this._oldIcon));
            } else {
                BufferedImage bi = new BufferedImage(this._background.getWidth(), this._background.getHeight(), 2);
                Graphics2D g2 = bi.createGraphics();
                g2.fillRect(0, 0, 0, 0);
                g2.drawImage(this._targetImage, null, 0, 0);
                g2.setComposite(AlphaComposite.getInstance(3, this._currentOpacity));
                g2.drawImage(this._oldIcon, null, 0, 0);
                g2.dispose();
                this._background.setIcon(new ImageIcon(bi));
            }
        }
        return backAnimating;
    }

    public synchronized void resetDisplayedHabitat() {
        this._displayedHabitat = -1.0;
    }

    public synchronized void setupBack(PhysicalState digimon, int scale) {
        this.setupBack(null, false, digimon, scale);
    }

    private synchronized void setupBack(String file, boolean force, PhysicalState digimon, int scale) {
        this._background.setLoc(0, 0);
        this.setBackground(file, digimon, scale, force);
        this._background.setSize(ViewConfig._habitatDimensions[0], ViewConfig._habitatDimensions[1]);
    }

    public synchronized void checkBack(PhysicalState digimon, Enum.Menu m, int scale, Battle battle, int habitat) {
        this.checkBack(digimon, m, scale, battle, false, habitat);
    }

    public synchronized void checkBack(PhysicalState digimon, Enum.Menu m, int scale, Battle battle) {
        this.checkBack(digimon, m, scale, battle, false, -1);
    }

    public synchronized void checkBackNoAnim(PhysicalState digimon, Enum.Menu m, int scale, Battle battle) {
        this.checkBack(digimon, m, scale, battle, true, -1);
    }

    public synchronized void checkBackNoAnim(PhysicalState digimon, Enum.Menu m, int scale, Battle battle, int habitat) {
        this.checkBack(digimon, m, scale, battle, true, habitat);
    }

    private synchronized void checkBack(PhysicalState digimon, Enum.Menu m, int scale, Battle battle, boolean force, int habitat) {
        if (ViewUtil.containsMenu(ViewUtil.FIRST_AID, m)) {
            if (force) {
                this.setupBack("firstAidBack.png", force, digimon, scale);
                this.resetDisplayedHabitat();
            }
        } else if (m == Enum.Menu.Habitat_Shop && habitat < 0 || Utility.containsState(ViewUtil.TRANSACTION_ANIM, digimon.getCurrentState()) || ViewUtil.containsMenu(ViewUtil.SHOP, m)) {
            this.setupBack("shop.png", force, digimon, scale);
            this.resetDisplayedHabitat();
        } else if (habitat >= 0) {
            this.changeHabitat(digimon.getHabitats().get(habitat), force, digimon, scale);
        } else if (ViewUtil.containsMenu(ViewUtil.DIGICORE, m) || Utility.containsState(ViewUtil.DIGICORE_ANIM, digimon.getCurrentState())) {
            if (m == Enum.Menu.EvolutionState) {
                this.setupBack(ViewUtil.getDigicoreBackground(digimon), force, digimon, scale);
            }
            this.resetDisplayedHabitat();
        } else if (digimon.getTournament().getActive() || battle != null && battle.getInProgress() && battle.getBattleType() == Battle.BattleType.PvP) {
            this.setupBack("tourneyBack.png", force, digimon, scale);
            this.resetDisplayedHabitat();
        } else if (digimon.getCurrentState() != Enum.State.WhaTransport) {
            Habitat h = digimon.getCurrentHabitat();
            this.changeHabitat(h, force, digimon, scale);
        } else {
            this.changeHabitat(digimon.getHabitats().get(8), force, digimon, scale);
        }
    }

    private synchronized void changeHabitat(Habitat h, boolean force, PhysicalState digimon, int scale) {
        double current = (double)h.getID() + (double)this.getBackgroundIndex(digimon) / 10.0;
        if (current != this._displayedHabitat) {
            this._displayedHabitat = h.getID();
            this.setupBack(h.getFileName(), force, digimon, scale);
        }
    }

    private synchronized void setBackground(String file, PhysicalState digimon, int scale, boolean force) {
        if (force) {
            this._currentOpacity = 0.0f;
            this._rate = 1.0;
            this.setBackground(digimon, file, scale);
        } else {
            this.setBackground(digimon, file, scale);
        }
    }

    private synchronized void setBackground(PhysicalState digimon, String file, int scale) {
        int[] i = this.getBackgroundTint(digimon);
        this.setAnimValues(i[0], i[1], i[2], this.getBackgroundIconFromSheet(file, digimon, scale));
    }

    private synchronized BufferedImage getBackgroundIconFromSheet(String file, PhysicalState digimon, int scale) {
        if (file != null) {
            BufferedImage sheet = ViewUtil.createBuffImage(ViewUtil.resizeImage(ViewUtil.getResource(this.MOD_FOLDER, this.RESOURCES_FOLDER, file), (double)scale));
            int y = 0;
            if (sheet.getHeight() > ViewConfig._habitatDimensions[1] * scale) {
                int index = this.getBackgroundIndex(digimon);
                this._displayedHabitat += (double)index / 10.0;
                int pad = 2 * scale;
                y = (pad *= index) + index * (ViewConfig._habitatDimensions[1] * scale);
            }
            return sheet.getSubimage(0, y, ViewConfig._habitatDimensions[0] * scale, ViewConfig._habitatDimensions[1] * scale);
        }
        return null;
    }

    private synchronized int getBackgroundIndex(PhysicalState digimon) {
        switch (digimon.getCurrentWeather()) {
            case Cloudy: 
            case Clear: {
                switch (digimon.checkTime(digimon.getClock().getHours())) {
                    case Night: {
                        return 3;
                    }
                    case Noon: {
                        if (digimon.isSunset(Enum.Time.Noon)) {
                            return 2;
                        }
                        return 1;
                    }
                }
                return 0;
            }
        }
        return 4;
    }

    private synchronized int[] getBackgroundTint(PhysicalState digimon) {
        int red = 0;
        int blue = 0;
        int alpha = 0;
        Enum.Weather weather = digimon.getCurrentWeather();
        if (weather != Enum.Weather.Clear) {
            alpha = 40;
            if (weather != Enum.Weather.Cloudy) {
                switch (digimon.checkTime(digimon.getClock().getHours())) {
                    case Morning: {
                        blue = 80;
                        break;
                    }
                    case Noon: {
                        if (!digimon.isSunset(Enum.Time.Noon)) break;
                        red = 60;
                        break;
                    }
                    case Night: {
                        alpha += 40;
                    }
                }
            }
        }
        return new int[]{red, blue, alpha};
    }
}

