/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Enum;
import java.util.HashMap;
import java.util.Map;

public class FieldAffinity {
    private Map<Enum.Field, Map<Enum.Field, Integer>> _fields = new HashMap<Enum.Field, Map<Enum.Field, Integer>>();

    public Map<Enum.Field, Map<Enum.Field, Integer>> getFields() {
        return this._fields;
    }

    public void readFieldInfo(String[] info) {
        Enum.Field f = Enum.Field.valueOf(info[0]);
        this._fields.put(f, new HashMap());
        this._fields.get((Object)f).put(Enum.Field.None, Integer.parseInt(info[1]));
        this._fields.get((Object)f).put(Enum.Field.DragonsRoar, Integer.parseInt(info[2]));
        this._fields.get((Object)f).put(Enum.Field.DeepSaver, Integer.parseInt(info[3]));
        this._fields.get((Object)f).put(Enum.Field.JungleTrooper, Integer.parseInt(info[4]));
        this._fields.get((Object)f).put(Enum.Field.MetalEmpire, Integer.parseInt(info[5]));
        this._fields.get((Object)f).put(Enum.Field.NatureSpirit, Integer.parseInt(info[6]));
        this._fields.get((Object)f).put(Enum.Field.WindGuardian, Integer.parseInt(info[7]));
        this._fields.get((Object)f).put(Enum.Field.NightmareSoldier, Integer.parseInt(info[8]));
        this._fields.get((Object)f).put(Enum.Field.DarkArea, Integer.parseInt(info[9]));
        this._fields.get((Object)f).put(Enum.Field.VirusBuster, Integer.parseInt(info[10]));
    }
}

