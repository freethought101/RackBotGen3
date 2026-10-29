// Battery and energy accounting (02 §1, rackbot/energy.py): 4S 50.4 Wh pack, INA226 sign convention
// (+ = discharge, − = charging), CC/CV dock charger 16.8 V / 1.5 A.
import {BATTERY_WH, CHARGE_A, CHARGE_TAPER_A, V_EMPTY, V_FULL} from './spec.ts';

export class Battery {
  soc: number;
  ibat = 0; // A, + = discharge
  powerW = 0; // bus load
  whUsed = 0;
  whCharged = 0;
  whActive = 0; // discharge while a job runs
  history: {t: number; soc: number}[] = [];

  constructor(soc = 0.9) {
    this.soc = soc;
  }

  get vbat() {
    return V_EMPTY + (V_FULL - V_EMPTY) * this.soc;
  }

  /** Charger current available at this SOC: constant current, tapering in the CV phase above 95 %. */
  private chargeA() {
    if (this.soc >= 1) return 0;
    if (this.soc < 0.95) return CHARGE_A;
    return CHARGE_TAPER_A * 0.5 + (CHARGE_A - CHARGE_TAPER_A * 0.5) * ((1 - this.soc) / 0.05);
  }

  tick(dt: number, loadW: number, dockPower: boolean, active: boolean, t: number) {
    const v = this.vbat;
    this.powerW = loadW;
    // the charger feeds the bus: it carries the load first, the rest goes into the pack
    const chargerW = dockPower ? this.chargeA() * V_FULL + loadW : 0;
    const netW = loadW - chargerW; // + = from the battery
    this.ibat = netW / v;
    const wh = (netW * dt) / 3600;
    if (wh >= 0) {
      this.whUsed += wh;
      if (active) this.whActive += wh;
    } else {
      this.whCharged -= wh;
    }
    this.soc = Math.min(1, Math.max(0, this.soc - wh / BATTERY_WH));
    const last = this.history[this.history.length - 1];
    if (!last || t - last.t >= 5) {
      this.history.push({t, soc: this.soc});
      if (this.history.length > 720) this.history.shift();
    }
  }

  get charging() {
    return this.ibat < -0.01;
  }
}
