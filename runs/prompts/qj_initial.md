# Astra prompt: QJ 2655 initial model

你现在在 Blender 中建立一个可检查、可编辑的前进型蒸汽机车 QJ 2655 模型。请先读取项目参考资料索引，并以 `QJ-side`、`QJ-three-quarter`、`QJ-front-detail` 三组真实照片作为主要依据。

场景约定：车体纵向为 X 轴，轨道横向为 Y 轴，车轮落在轨道高度；本车放在左侧轨道。请建立独立的 `QJ_steam_locomotive` Collection，并保留清晰的父子层级。

必须分别建立并命名这些对象或对象组：车架、锅炉、烟箱、驾驶室、烟囱、汽包、车灯、扶手、主动轮、从动轮、轮轴、主连杆、侧连杆、制动结构、煤水车、车钩和缓冲器。每个对象都要能在 Outliner 中单独选择、隐藏、移动和编辑；禁止把整车合并成一个外壳再只改变材质。

请在对象自定义属性中写入 `subject`、`component_role`、`reference_ids`，并把无法从照片确认的尺寸标成近似值，不要虚构工程级精度。完成后先保存未经人工修改的 `v00_ai_initial.blend`，再导出一个保留层级的 GLB。不要进行人工修复，不要覆盖初始文件。
