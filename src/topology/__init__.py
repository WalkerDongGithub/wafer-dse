"""拓扑定义子包。

提供经典互连拓扑族：

    Topology (ABC)       拓扑抽象基类
    ├── Mesh             二维 mesh（无环绕）
    ├── Torus            二维 torus（有环绕）
    ├── KaryNCube        n 维 k-ary n-cube（Mesh/Torus 的泛化）
    └── Dragonfly        标准 Dragonfly（Cray Cascade 风格）
    └── DragonflyPlus    Dragonfly+ 骨架（待实现）

扩展方式：
    新增拓扑时在此目录新建文件，实现 Topology 接口，然后在 __init__.py 导出。
"""

from topology.base import Topology
from topology.dragonfly import Dragonfly, DragonflyPlus
from topology.kary_ncube import KaryNCube
from topology.mesh import Mesh
from topology.torus import Torus

__all__ = [
    "Dragonfly",
    "DragonflyPlus",
    "KaryNCube",
    "Mesh",
    "Topology",
    "Torus",
]
