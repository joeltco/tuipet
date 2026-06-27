/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.CurrentTime;
import Model.PhysicalState;
import Model.ViewSettings;

public class Controller {
    private CurrentTime _time;
    private PhysicalState _digimon;
    private ViewSettings _settings;

    public CurrentTime getTime() {
        return this._time;
    }

    public PhysicalState getDigimon() {
        return this._digimon;
    }

    public ViewSettings getSettings() {
        return this._settings;
    }

    public Controller(CurrentTime time, PhysicalState digimon, ViewSettings settings) {
        this._time = time;
        this._digimon = digimon;
        this._settings = settings;
    }
}

