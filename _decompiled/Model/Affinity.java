/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Enum;
import Model.JogressAttributePair;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class Affinity {
    private Map<Enum.Field, Map<Enum.Field, Integer>> _fields = new HashMap<Enum.Field, Map<Enum.Field, Integer>>();
    private Map<Enum.Element, Map<Enum.Element, Integer>> _elements = new HashMap<Enum.Element, Map<Enum.Element, Integer>>();
    private ArrayList<JogressAttributePair> _attributes = new ArrayList();

    public Map<Enum.Field, Map<Enum.Field, Integer>> getFields() {
        return this._fields;
    }

    public Map<Enum.Element, Map<Enum.Element, Integer>> getElements() {
        return this._elements;
    }

    public ArrayList<JogressAttributePair> getAttributes() {
        return this._attributes;
    }

    public String getPartnerAttributeAsString(Enum.Attribute evol, Enum.Attribute digimon) {
        String s = "";
        for (JogressAttributePair a : this._attributes) {
            if (a.getEvolutionAttribute() != evol || a.getDigimonAttribute() != digimon) continue;
            s = s + a.getPartnerAttribute().toString() + ",";
        }
        return s;
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

    public void readElementInfo(String[] info) {
        Enum.Element e = Enum.Element.valueOf(info[0]);
        this._elements.put(e, new HashMap());
        this._elements.get((Object)e).put(Enum.Element.Fire, Integer.parseInt(info[1]));
        this._elements.get((Object)e).put(Enum.Element.Light, Integer.parseInt(info[2]));
        this._elements.get((Object)e).put(Enum.Element.Ice, Integer.parseInt(info[3]));
        this._elements.get((Object)e).put(Enum.Element.Water, Integer.parseInt(info[4]));
        this._elements.get((Object)e).put(Enum.Element.Metal, Integer.parseInt(info[5]));
        this._elements.get((Object)e).put(Enum.Element.Wood, Integer.parseInt(info[6]));
        this._elements.get((Object)e).put(Enum.Element.Dark, Integer.parseInt(info[7]));
        this._elements.get((Object)e).put(Enum.Element.Thunder, Integer.parseInt(info[8]));
        this._elements.get((Object)e).put(Enum.Element.Earth, Integer.parseInt(info[9]));
        this._elements.get((Object)e).put(Enum.Element.Wind, Integer.parseInt(info[10]));
        this._elements.get((Object)e).put(Enum.Element.None, Integer.parseInt(info[11]));
    }

    public void readAttributeInfo(String[] info) {
        Enum.Attribute a = Enum.Attribute.valueOf(info[0]);
        try {
            this._attributes.add(new JogressAttributePair(Enum.Attribute.valueOf(info[1]), Enum.Attribute.None, a));
        }
        catch (ArrayIndexOutOfBoundsException | IllegalArgumentException runtimeException) {
            // empty catch block
        }
        try {
            this._attributes.add(new JogressAttributePair(Enum.Attribute.valueOf(info[2]), Enum.Attribute.Vaccine, a));
        }
        catch (ArrayIndexOutOfBoundsException | IllegalArgumentException runtimeException) {
            // empty catch block
        }
        try {
            this._attributes.add(new JogressAttributePair(Enum.Attribute.valueOf(info[3]), Enum.Attribute.Data, a));
        }
        catch (ArrayIndexOutOfBoundsException | IllegalArgumentException runtimeException) {
            // empty catch block
        }
        try {
            this._attributes.add(new JogressAttributePair(Enum.Attribute.valueOf(info[4]), Enum.Attribute.Virus, a));
        }
        catch (ArrayIndexOutOfBoundsException | IllegalArgumentException runtimeException) {
            // empty catch block
        }
    }

    public ArrayList<JogressAttributePair> getJogressCombinations(Enum.Attribute a) {
        ArrayList<JogressAttributePair> list = new ArrayList<JogressAttributePair>();
        for (JogressAttributePair j : this._attributes) {
            if (j.getEvolutionAttribute() != a) continue;
            list.add(j);
        }
        ArrayList<JogressAttributePair> retain = new ArrayList<JogressAttributePair>();
        Iterator iterator = list.iterator();
        while (iterator.hasNext()) {
            JogressAttributePair j;
            JogressAttributePair test = j = (JogressAttributePair)iterator.next();
            for (JogressAttributePair repeat : list) {
                if (retain.contains(test) || test.getDigimonAttribute() != repeat.getPartnerAttribute() || test.getPartnerAttribute() != repeat.getDigimonAttribute()) continue;
                retain.add(repeat);
            }
        }
        return retain;
    }
}

