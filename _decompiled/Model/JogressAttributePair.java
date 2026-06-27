/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Enum;

public class JogressAttributePair {
    private final Enum.Attribute _evolution;
    private final Enum.Attribute _digimon;
    private final Enum.Attribute _partner;

    public Enum.Attribute getEvolutionAttribute() {
        return this._evolution;
    }

    public Enum.Attribute getDigimonAttribute() {
        return this._digimon;
    }

    public Enum.Attribute getPartnerAttribute() {
        return this._partner;
    }

    public JogressAttributePair(Enum.Attribute evol, Enum.Attribute digimon, Enum.Attribute partner) {
        this._evolution = evol;
        this._digimon = digimon;
        this._partner = partner;
    }
}

