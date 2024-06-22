import { Theme, createStyles } from "@mui/material/styles";
import { makeStyles } from "@mui/styles";
import { feedListWidth } from "../../const";

export default makeStyles((theme: Theme) =>
  createStyles({
    appBar: {
      transition: theme.transitions.create(["margin", "width"], {
        easing: theme.transitions.easing.sharp,
        duration: theme.transitions.duration.leavingScreen,
      }),
    },
    appBarShift: {
      width: `calc(100% - ${feedListWidth}px)`,
      marginLeft: feedListWidth,
      transition: theme.transitions.create(["margin", "width"], {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
      }),
    },
    hide: {
      display: "none",
    },
    toolbar: {
      justifyContent: "space-between",
    },
    logoutButton: {
      marginRight: -15
    },
    burgeredMenu: {
      "& .MuiPopover-paper": {
        left: "0px !important",
        width: "calc(100%)",
        maxWidth: "none",
        marginTop: 41,
        borderRadius: 0,
      }
    }
  }),
);
