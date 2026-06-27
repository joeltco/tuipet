/*
 * Decompiled with CFR 0.152.
 */
package View;

import View.Frame;
import View.SpriteObjWIP;
import java.util.ArrayList;

public class Animation {
    private ArrayList<Frame> _animation = new ArrayList();
    private boolean _loop;
    private int _currentFrame;
    private SpriteObjWIP _object;
    private boolean _paused;

    public boolean getPaused() {
        return this._paused;
    }

    public void setPaused(boolean p) {
        this._paused = p;
    }

    public Animation(SpriteObjWIP obj, boolean loop) {
        this._object = obj;
        this._loop = loop;
    }

    public void animate() {
        if (!this._paused) {
            if (this._currentFrame < this._animation.size()) {
                Frame frame = this._animation.get(this._currentFrame);
                if (!frame.draw()) {
                    ++this._currentFrame;
                }
            } else if (this._loop) {
                this.reset();
                this.animate();
            }
        }
    }

    public void setVisible(boolean v) {
        this._object.setVisible(v);
    }

    public void reset() {
        this._currentFrame = 0;
        for (int i = this._animation.size() - 1; i >= 0; --i) {
            this._animation.get(i).reset();
        }
    }

    public void addFrame(String imageName, int duration, int x, int y) {
        this._animation.add(new Frame(this._object, imageName, 0, false, duration, x, y, true));
    }

    public void addFrame(String imageName, int duration) {
        this._animation.add(new Frame(this._object, imageName, 0, false, duration, 0, 0, false));
    }

    public void addFrame(int spriteNum, boolean mirrored, int duration, int x, int y) {
        this._animation.add(new Frame(this._object, "", spriteNum, mirrored, duration, x, y, true));
    }

    public void addFrame(int spriteNum, boolean mirrored, int duration) {
        this._animation.add(new Frame(this._object, "", spriteNum, mirrored, duration, 0, 0, false));
    }
}

