# 参考图坦克 Blender 可编辑模型

主文件：`models/leopard2/Leopard_2_early_prototype_editable.blend`。同目录的 `.glb` 用于交换和快速预览；六张预览图位于 `assets/leopard2/`。继续建模和调整结构时使用 `.blend`。

## 原型与依据

外形以用户提供的四向视图为主。图题、车体比例、七对负重轮、尾部双圆形风扇和焊接炮塔支持“早期豹2原型车”的判断。补充资料用于解释未标注的外部细节，尚不足以确定具体 PT 车体号、T 炮塔号或炮管口径。PT15/T02 照片属于同类原型车参照，不代表参考图已经被确认是该车。

原始四向图保存在 `references/leopard2/reference_four_views.png`。来源、作者、许可和文件 SHA256 见 `references/leopard2/reference-index.json`；研究过程及尺寸解释见同目录的 `source-research.md`。附带的 Sonaz 照片适用 CC BY 3.0，Yuma 照片的来源页面将其标注为美国联邦政府作品、在美国属于公有领域。用户四向图的原作者和公开许可未提供。

## 坐标与编辑

- 场景以米为单位；`+Z` 向上，`-X` 为车头与炮口方向，`Y` 为横向。
- `Model_Root` 管理整车变换，适合整体移动、旋转及统一缩放。
- `Turret_Pivot` 的自定义属性 `yaw_degrees` 控制炮塔水平转角。
- `Gun_Elevation_Pivot` 的自定义属性 `elevation_degrees` 控制炮管俯仰角。
- 车体、炮塔、炮管、行走机构及外部附件保留为独立对象。履带使用重复链接部件；修改共享网格会影响其他链接实例，需要单独修改时先将对象数据设为单用户。
- 绳索等曲线对象保留曲线结构。倒角和材质可继续调整；GLB 不完整保留 Blender 的曲线、修改器与自定义控制关系。

## 比例目标与误差说明

以下数值为参考图解释后的建模目标，不替代最终几何校验报告。

| 项目 | 目标值 | 依据 |
| --- | ---: | --- |
| 炮管朝前的整车总长 | 9.613 m | 图中总长尺寸优先 |
| 车体及挡泥板纵向包络 | 7.672 m | 图中标注 |
| 最大横向包络 | 3.700 m | 图中外层宽度标注 |
| 炮轴离地高度 | 2.009 m | 图中标注 |
| 单条履带宽度 | 0.635 m | 图中标注 |
| 履带中心距 | 2.785 m | 与 3.420 m 外宽相互核对 |
| 履带外宽 | 3.420 m | 2.785 + 0.635 m |

图中“炮口至炮塔参考线 5.218 m”加“参考线至车尾 4.400 m”得到 9.618 m，与总长 9.613 m 相差 5 mm。模型按总长标注确定主包络，将该差异视为图纸标注或扫描读取误差；不同时宣称两个互相矛盾的长度都精确成立。

图上 2.884 m 高度及其他竖向标注的端点需要结合视图理解，不能直接当作包含全部天线的最终整车高度。突出天线、机枪及设备的位置按图形补充，最终高度以模型几何校验为准。

图纸未给出履带节距、连接销、螺栓、轮毂剖面、装甲厚度、附件截面及隐藏表面的完整尺寸。这些部分采用外观合理的估计。模型用于外观展示与后续编辑，不包含经验证的真实内部结构或机械设计。

## 最终文件检查

已使用 Blender 5.2.1 LTS 重新打开交付文件，29 项检查全部通过。实际外包络为长 9.613 m、宽 3.700 m、含外部桅杆高 3.358 m；炮轴高度为 2.009 m。履带节的最低角点已贴合 Z=0 地面。

模型包含 1,916 个对象，其中 1,831 个网格对象、26 个可编辑曲线对象；两侧共 170 节独立履带对象、28 个负重轮轮体。倒角后的显示几何约 453,552 个三角面。模型未合并成单个壳体，也未烘焙掉 Blender 中的分件和修改器。

已实际测试炮塔转动 32 度与炮管俯仰 12 度，并核对附属部件的跟随关系以及恢复零位后的坐标。完整数据见 `models/leopard2/validation_report.json`；六视角图见 `assets/leopard2/model_contact_sheet.jpg`。

## 重新生成

在项目根目录运行，先生成模型，再独立打开检查：

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python scripts/build_leopard2_reference.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background models/leopard2/Leopard_2_early_prototype_editable.blend --python-exit-code 1 --python scripts/validate_leopard2_model.py
```

渲染相机与灯光位于 `99 | Studio cameras and lighting (not model)` 集合，可以关闭该集合后继续编辑纯模型。原始四向图已内嵌在 Blender 文件中，位于默认隐藏的 `90 | Packed reference drawing (toggle visibility)` 集合。主要模型无需外部纹理；GLB 交换文件采用简化材质，不保留全部程序材质细节。
