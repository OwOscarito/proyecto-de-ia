from enum import Enum


class Fase(Enum):
    VERDE_VEHICULAR = "Verde vehicular"
    AMARILLO = "Amarillo"
    VERDE_PEATONAL = "Verde peatonal"
    TODO_ROJO = "Todo rojo"


class SemaforoAdaptativo:
    def __init__(self, fps):
        self.fps = fps
        self.T_AMARILLO = 3
        self.T_TODO_ROJO = 2
        self.T_VEH_MIN = 10
        self.T_VEH_MAX = 60
        self.T_PEAT_MIN = 8
        self.T_PEAT_MAX = 40
        self.fase = Fase.VERDE_VEHICULAR
        self.tiempo_restante = self.T_VEH_MIN
        self.hist_veh = []
        self.hist_peat = []
        self.VENTANA = 30

    def _avg(self, lst):
        return sum(lst) / max(len(lst), 1)

    def _t_veh(self):
        return max(
            self.T_VEH_MIN,
            min(self.T_VEH_MIN + int(self._avg(self.hist_veh) * 4), self.T_VEH_MAX),
        )

    def _t_peat(self):
        return max(
            self.T_PEAT_MIN,
            min(self.T_PEAT_MIN + int(self._avg(self.hist_peat) * 3), self.T_PEAT_MAX),
        )

    def tick(self, n_veh, n_peat):
        self.hist_veh.append(n_veh)
        self.hist_peat.append(n_peat)

        if len(self.hist_veh) > self.VENTANA:
            self.hist_veh.pop(0)
            self.hist_peat.pop(0)

        self.tiempo_restante -= 1 / self.fps

        if self.tiempo_restante <= 0:
            self._siguiente()

        return {
            "fase": self.fase.value,
            "tiempo_restante": round(max(0, self.tiempo_restante), 1),
            "avg_veh": round(self._avg(self.hist_veh), 1),
            "avg_peat": round(self._avg(self.hist_peat), 1),
            "t_veh_calc": self._t_veh(),
            "t_peat_calc": self._t_peat(),
        }

    def _siguiente(self):
        if self.fase == Fase.VERDE_VEHICULAR:
            self.fase = Fase.AMARILLO
            self.tiempo_restante = self.T_AMARILLO

        elif self.fase == Fase.AMARILLO:
            self.fase = Fase.TODO_ROJO
            self.tiempo_restante = self.T_TODO_ROJO

        elif self.fase == Fase.TODO_ROJO:
            if self._avg(self.hist_peat) > 1:
                self.fase = Fase.VERDE_PEATONAL
                self.tiempo_restante = self._t_peat()
            else:
                self.fase = Fase.VERDE_VEHICULAR
                self.tiempo_restante = self._t_veh()

        elif self.fase == Fase.VERDE_PEATONAL:
            self.fase = Fase.TODO_ROJO
            self.tiempo_restante = self.T_TODO_ROJO
