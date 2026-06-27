/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Zone;
import java.util.ArrayList;

public class MapLevel {
    private ArrayList<Zone> _zones = new ArrayList();
    private boolean _isComplete;
    private boolean _isCurrent;
    private boolean _isUnlocked;
    private int _mapNum;
    private String _image;

    public ArrayList<Zone> getZones() {
        return this._zones;
    }

    public Zone getZone(int num) {
        for (Zone z : this._zones) {
            if (z.getZoneNum() != num) continue;
            return z;
        }
        return null;
    }

    public Zone[] getTravelZones() {
        ArrayList<Zone> maps = new ArrayList<Zone>();
        for (int i = 1; i < this._zones.size(); ++i) {
            if (!this._zones.get(i).getIsUnlocked() || this._zones.get(i).getIsCurrent()) continue;
            maps.add(this._zones.get(i));
        }
        Zone[] m = new Zone[maps.size()];
        return maps.toArray(m);
    }

    public void setIsComplete(boolean newComplete) {
        this._isComplete = newComplete;
    }

    public boolean getIsComplete() {
        return this._isComplete;
    }

    public void setIsCurrent(boolean newCurrent) {
        this._isCurrent = newCurrent;
    }

    public boolean getIsCurrent() {
        return this._isCurrent;
    }

    public void setIsUnlocked(boolean newUnlocked) {
        this._isUnlocked = newUnlocked;
    }

    public boolean getIsUnlocked() {
        return this._isUnlocked;
    }

    public void setMapNum(int newNum) {
        this._mapNum = newNum;
    }

    public int getMapNum() {
        return this._mapNum;
    }

    public String getImage() {
        return this._image;
    }

    public MapLevel() {
    }

    public MapLevel(int mapNum) {
        this._mapNum = mapNum;
        this._isCurrent = false;
        this._isComplete = false;
    }

    public void addZone(Zone zone) {
        if (!this._zones.contains(zone)) {
            this._zones.add(zone);
        }
    }

    public MapLevel readInfoString(String map) {
        String[] info = map.split(",");
        this._mapNum = Integer.parseInt(info[0]);
        this._image = info[1];
        this._isUnlocked = Boolean.parseBoolean(info[2]);
        return this;
    }

    public String infoToString() {
        StringBuilder info = new StringBuilder();
        String delin = ",";
        info.append(this._mapNum);
        return info.toString();
    }
}

