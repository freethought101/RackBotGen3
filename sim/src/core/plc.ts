// The rack PLC (Delta DVP-12SE) as 03 §4 describes it: D0 inputs, D1 outputs, D2 heartbeat, D3 state, and the
// ladder: Y0 = M0 AND X4 AND X5 AND NOT M10; RED = NOT X5 OR M10 OR M2; YELLOW = M1 AND NOT RED; GREEN otherwise.

export type PlcInputs = {bays: boolean[]; dock: boolean; estopOk: boolean; s1: boolean; s2: boolean};

export class Plc {
  // coils written by the Pi over Modbus
  M0 = false; // dock power request
  M1 = false; // lamp YELLOW request
  M2 = false; // lamp RED request (robot fault)
  M10 = false; // Pi watchdog lost (never in the sim)
  D2 = 0; // heartbeat, +1 every 100 ms
  private acc = 0;
  x: PlcInputs = {bays: [true, true, true, true], dock: true, estopOk: true, s1: true, s2: false};

  scan(dt: number, inputs: PlcInputs) {
    this.x = inputs;
    this.acc += dt;
    while (this.acc >= 0.1) {
      this.acc -= 0.1;
      this.D2 = (this.D2 + 1) & 0xffff;
    }
  }

  get D0() {
    const {bays, dock, estopOk, s1, s2} = this.x;
    return bays.reduce((m, b, i) => m | (b ? 1 << i : 0), 0) | (dock ? 16 : 0) | (estopOk ? 32 : 0) | (s1 ? 64 : 0) | (s2 ? 128 : 0);
  }

  get Y0() {
    return this.M0 && this.x.dock && this.x.estopOk && !this.M10;
  }

  get lamp(): 'red' | 'amber' | 'green' {
    if (!this.x.estopOk || this.M10 || this.M2) return 'red';
    if (this.M1) return 'amber';
    return 'green';
  }

  get D1() {
    const l = this.lamp;
    return (this.Y0 ? 1 : 0) | (l === 'green' ? 2 : 0) | (l === 'amber' ? 4 : 0) | (l === 'red' ? 8 : 0);
  }

  get D3() {
    return !this.x.estopOk ? 1 : this.M10 ? 2 : 0;
  }
}
