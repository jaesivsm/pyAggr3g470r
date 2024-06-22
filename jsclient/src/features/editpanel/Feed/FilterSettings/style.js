import { Theme, createStyles } from "@mui/material/styles";
import { makeStyles } from "@mui/styles";

export default makeStyles((theme: Theme) =>
  createStyles({
    editPanelFilter: {
      display: "table",
      alignItems: "baseline",
      flexDirection: "row",
      marginBottom: 25,
      marginLeft: 16,
      marginRight: 16
    },
    editPanelFilterItem: {
      display: "table-cell",
      "& .MuiInput-root": {
        height: 32,
        justifyContent: "center"
      },
      "& .MuiTextField-root": {
        height: 32,
        justifyContent: "center",
        "& input": {
          padding: 0
        }
      }
    },
    editPanelFilterArrows: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      left: 5,
      position: "absolute"
    },
    editPanelFilterArrow: {
      position: "relative",
      padding: 0,
      "& svg": {
        height: 18,
        width: 18,
      }
    },
    editPanelFilterAddBtn: {
      textAlign: "center",
      width: "100%",
      "& button": {
        minHeight: "unset",
        height: 35,
        width: 35,
      }
    },
    editPanelFilterDelBtn: {
      position: "absolute",
      right: 0,
      padding: 8,
      "& svg": {
        height: 18,
        width: 18
      }
    },
  }),
);
